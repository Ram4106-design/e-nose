use influxdb2::Client;
use influxdb2::models::DataPoint;
use tokio::sync::mpsc;
use anyhow::Result;
use futures_util::stream;

// === Data Structure ===
#[derive(Debug, Clone)]
pub struct UnifiedSensorData {
    pub no2: f32,
    pub eth: f32,
    pub voc: f32,
    pub co: f32,
    pub com: f32,
    pub ethm: f32,
    pub vocm: f32,
    pub state: i32,
    pub level: i32,
    pub timestamp: i64,  // in nanoseconds
    pub source: String,
}

// === InfluxDB Handler ===
#[derive(Clone)]
pub struct InfluxDBHandler {
    tx: mpsc::Sender<UnifiedSensorData>,
}

impl InfluxDBHandler {
    pub fn new(url: &str, token: &str, org: &str, bucket: &str) -> Self {
        let client = Client::new(url, org, token);  // Note: order is url, org, token
        
        let (tx, mut rx) = mpsc::channel::<UnifiedSensorData>(100);
        
        let client_clone = client.clone();
        let bucket_string = bucket.to_string();
        
        // Spawn background task untuk menulis ke InfluxDB
        tokio::spawn(async move {
            println!("📊 InfluxDB writer task started");
            
            while let Some(data) = rx.recv().await {
                // Build DataPoint dengan measurement name "sensors"
                let point = DataPoint::builder("sensors")
                    .tag("source", data.source.clone())
                    .field("no2", data.no2 as f64)
                    .field("eth", data.eth as f64)
                    .field("voc", data.voc as f64)
                    .field("co", data.co as f64)
                    .field("com", data.com as f64)
                    .field("ethm", data.ethm as f64)
                    .field("vocm", data.vocm as f64)
                    .field("state", data.state as i64)
                    .field("level", data.level as i64)
                    .timestamp(data.timestamp)  // timestamp harus dalam nanoseconds
                    .build();
                
                match point {
                    Ok(p) => {
                        let stream = stream::once(async move { p });
                        
                        match client_clone.write(&bucket_string, stream).await {
                            Ok(_) => {
                                // Uncomment untuk debug
                                // println!("✅ Data written to InfluxDB");
                            }
                            Err(e) => {
                                eprintln!("❌ InfluxDB write error: {:?}", e);
                            }
                        }
                    }
                    Err(e) => {
                        eprintln!("❌ DataPoint build error: {:?}", e);
                    }
                }
            }
            
            println!("⚠️ InfluxDB writer task exited");
        });
        
        Self { tx }
    }
    
    pub async fn send(&self, data: UnifiedSensorData) -> Result<()> {
        self.tx.send(data).await?;
        Ok(())
    }
}