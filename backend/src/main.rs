use tokio::{
    io::{AsyncBufReadExt, BufReader, AsyncWriteExt},
    net::{TcpListener, TcpStream},
    sync::broadcast,
};
use serde::Serialize;
use anyhow::Result;
use chrono::Utc;
use dotenv::dotenv;
use std::env;

mod filtering;
use filtering::{SensorFilters, FilterConfig, UnifiedSensorRaw};

mod influxdb;
use influxdb::{InfluxDBHandler, UnifiedSensorData as InfluxData};

fn create_filters() -> SensorFilters {
    let config = FilterConfig::load("config.toml");
    SensorFilters::new(&config)
}

/// Map state integer to readable state name
fn state_to_name(state: i32) -> String {
    match state {
        0 => "IDLE",
        1 => "PRE_COND",
        2 => "RAMP_UP",
        3 => "HOLD",
        4 => "PURGE",
        5 => "RECOVERY",
        6 => "DONE",
        _ => "UNKNOWN",
    }.to_string()
}

#[derive(Serialize, Debug, Clone)]
struct UnifiedSensorData {
    no2: f32,
    eth: f32,
    voc: f32,
    co: f32,
    com: f32,
    ethm: f32,
    vocm: f32,
    state: i32,
    state_name: String,
    level: i32,
    timestamp: i64,
    source: String,
}

#[tokio::main]
async fn main() -> Result<()> {
    println!("🟢 E-Nose Rust Backend Starting...");
    
    // Load environment variables (optional)
    dotenv().ok();

    let filters = create_filters();

    // Try to get from env, fallback to hardcoded
    let influx_url = env::var("INFLUXDB_URL").unwrap_or_else(|_| "http://localhost:8086".to_string());
    let influx_token = env::var("INFLUXDB_TOKEN").unwrap_or_else(|_| {
        // ⚠️ GANTI INI DENGAN TOKEN BARU DARI INFLUXDB!
        "YFwmMyQPO9BqaLrw9HKqlRxUYWWbD0Fulfbr_OgmDuZiCpABq64ch5xn_b8g1lSM4Ow65pci4iFdDMpqf0l_vw==".to_string()
    });
    let influx_org = env::var("INFLUXDB_ORG").unwrap_or_else(|_| "011a1a9099df7a18".to_string());
    let influx_bucket = env::var("INFLUXDB_BUCKET").unwrap_or_else(|_| "E-Nose".to_string());
    
    println!("📊 InfluxDB Config:");
    println!("   URL: {}", influx_url);
    println!("   Org: {}", influx_org);
    println!("   Bucket: {}", influx_bucket);
    if influx_token.len() > 30 {
        println!("   Token: {}...{}", &influx_token[..15], &influx_token[influx_token.len()-10..]);
    }

    let influx = InfluxDBHandler::new(
        &influx_url,
        &influx_token,
        &influx_org,
        &influx_bucket,
    );

    // Channel untuk broadcast data sensor ke GUI
    let (data_tx, _rx) = broadcast::channel::<String>(100);
    
    // Channel untuk command dari GUI ke Arduino
    let (cmd_tx, _cmd_rx) = broadcast::channel::<String>(10);

    // Server GUI (TCP 8082)
    tokio::spawn(gui_server(data_tx.clone(), cmd_tx.clone()));

    // Server untuk Arduino (TCP 8081)
    let listener = TcpListener::bind("0.0.0.0:8081").await?;
    println!("🔌 Listening for Arduino on 0.0.0.0:8081");

    loop {
        let (stream, addr) = listener.accept().await?;
        println!("✅ Arduino connected: {}", addr);

        let data_tx_clone = data_tx.clone();
        let cmd_rx = cmd_tx.subscribe();
        let influx_clone = influx.clone();
        let mut filters_clone = filters.clone();

        tokio::spawn(async move {
            handle_arduino(stream, data_tx_clone, cmd_rx, &mut filters_clone, influx_clone).await;
        });
    }
}

// ================= Arduino Handler =================
async fn handle_arduino(
    stream: TcpStream,
    data_tx: broadcast::Sender<String>,
    mut cmd_rx: broadcast::Receiver<String>,
    filters: &mut SensorFilters,
    influx: InfluxDBHandler,
) {
    println!("🔧 Arduino handler started");
    let (reader, mut writer) = stream.into_split();
    let mut lines = BufReader::new(reader).lines();

    println!("📡 Arduino handler waiting for commands and data...");

    // Spawn dedicated task untuk handle commands
    let write_handle = tokio::spawn(async move {
        while let Ok(command) = cmd_rx.recv().await {
            println!("📤 Received command for Arduino: '{}'", command);
            
            let cmd_with_newline = format!("{}\n", command);
            
            match writer.write_all(cmd_with_newline.as_bytes()).await {
                Ok(_) => println!("✅ Command written to Arduino"),
                Err(e) => {
                    eprintln!("❌ Failed to write command to Arduino: {}", e);
                    break;
                }
            }
            
            match writer.flush().await {
                Ok(_) => println!("✅ Command flushed to Arduino successfully"),
                Err(e) => {
                    eprintln!("❌ Failed to flush command to Arduino: {}", e);
                    break;
                }
            }
        }
        println!("⚠️ Command handler exited");
    });

    // Main loop hanya baca dari Arduino
    loop {
        match lines.next_line().await {
            Ok(Some(line)) => {
                if line.starts_with("SENSOR:") {
                    process_arduino_line(&line, &data_tx, filters, &influx).await;
                } else {
                    println!("📝 Arduino: {}", line);
                }
            }
            Ok(None) => {
                println!("❌ Arduino disconnected (EOF)");
                break;
            }
            Err(e) => {
                eprintln!("❌ Arduino read error: {}", e);
                break;
            }
        }
    }

    write_handle.abort();
    println!("❌ Arduino handler exited");
}

async fn process_arduino_line(
    line: &str,
    data_tx: &broadcast::Sender<String>,
    filters: &mut SensorFilters,
    influx: &InfluxDBHandler,
) {
    let data_str = line.trim_start_matches("SENSOR:");
    let values: Vec<f32> = data_str
        .split(',')
        .filter_map(|s| s.parse::<f32>().ok())
        .collect();

    if values.len() < 9 {
        return;
    }

    let raw = UnifiedSensorRaw {
        no2: values[0],
        eth: values[1],
        voc: values[2],
        co: values[3],
        com: values[4],
        ethm: values[5],
        vocm: values[6],
        state: values[7] as i32,
        level: values[8] as i32,
    };

    let filtered = filters.update(&raw);

    let payload = UnifiedSensorData {
        no2: filtered.no2,
        eth: filtered.eth,
        voc: filtered.voc,
        co: filtered.co,
        com: filtered.com,
        ethm: filtered.ethm,
        vocm: filtered.vocm,
        state: filtered.state,
        state_name: state_to_name(filtered.state),
        level: filtered.level,
        timestamp: Utc::now().timestamp_millis(),
        source: "arduino".to_string(),
    };

    // Kirim JSON ke GUI
    if let Ok(json) = serde_json::to_string(&payload) {
        let _ = data_tx.send(json);
    }

    // Kirim ke InfluxDB
    let _ = influx
        .send(InfluxData {
            no2: payload.no2,
            eth: payload.eth,
            voc: payload.voc,
            co: payload.co,
            com: payload.com,
            ethm: payload.ethm,
            vocm: payload.vocm,
            state: payload.state,
            level: payload.level,
            timestamp: payload.timestamp * 1_000_000,
            source: payload.source.clone(),
        })
        .await;
}

// ================= GUI Server =================
async fn gui_server(
    data_tx: broadcast::Sender<String>,
    cmd_tx: broadcast::Sender<String>,
) -> Result<()> {
    let listener = TcpListener::bind("0.0.0.0:8082").await?;
    println!("📡 GUI server listening on 0.0.0.0:8082");
    println!("📊 Command channel receiver count: {}", cmd_tx.receiver_count());

    loop {
        let (socket, addr) = listener.accept().await?;
        let mut data_rx = data_tx.subscribe();
        let cmd_tx_clone = cmd_tx.clone();
        println!("✅ GUI connected: {}", addr);
        println!("📊 Active receivers: {}", cmd_tx.receiver_count());

        tokio::spawn(async move {
            let (reader, mut writer) = socket.into_split();
            let mut lines = BufReader::new(reader).lines();

            loop {
                tokio::select! {
                    // Kirim data sensor ke GUI
                    Ok(msg) = data_rx.recv() => {
                        let data_with_newline = format!("{}\n", msg);
                        if writer.write_all(data_with_newline.as_bytes()).await.is_err() {
                            println!("❌ Failed to write to GUI");
                            break;
                        }
                        if writer.flush().await.is_err() {
                            println!("❌ Failed to flush to GUI");
                            break;
                        }
                    }
                    
                    // Terima command dari GUI
                    result = lines.next_line() => {
                        match result {
                            Ok(Some(cmd)) => {
                                let cmd = cmd.trim().to_string();
                                if !cmd.is_empty() {
                                    println!("📥 GUI command received: '{}'", cmd);
                                    println!("📊 Broadcasting to {} receivers", cmd_tx_clone.receiver_count());
                                    
                                    // Forward command ke Arduino
                                    match cmd_tx_clone.send(cmd.clone()) {
                                        Ok(count) => println!("✅ Command broadcasted to {} receivers", count),
                                        Err(e) => eprintln!("❌ Failed to broadcast command: {}", e),
                                    }
                                }
                            }
                            Ok(None) => {
                                println!("❌ GUI disconnected (EOF)");
                                break;
                            }
                            Err(e) => {
                                eprintln!("❌ GUI read error: {}", e);
                                break;
                            }
                        }
                    }
                }
            }
            
            println!("❌ GUI handler exited: {}", addr);
        });
    }
}