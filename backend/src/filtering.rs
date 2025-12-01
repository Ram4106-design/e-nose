use serde::Deserialize;
use std::time::SystemTime;

#[derive(Debug, Deserialize, Clone)]
pub struct FilterConfig {
    pub window_size: usize,
    #[serde(default = "default_sine_amplitude")]
    pub sine_amplitude: f32,
    #[serde(default = "default_sine_frequency")]
    pub sine_frequency: f32,
    #[serde(default = "default_sine_enabled")]
    pub sine_enabled: bool,
}

fn default_sine_amplitude() -> f32 { 0.15 }  // 15% amplitude
fn default_sine_frequency() -> f32 { 0.5 }   // 0.5 Hz (1 cycle per 2 seconds)
fn default_sine_enabled() -> bool { true }

impl FilterConfig {
    pub fn load(path: &str) -> Self {
        let content = std::fs::read_to_string(path).unwrap_or_default();
        toml::from_str(&content).unwrap_or(Self { 
            window_size: 5,
            sine_amplitude: default_sine_amplitude(),
            sine_frequency: default_sine_frequency(),
            sine_enabled: default_sine_enabled(),
        })
    }
}

// Data mentah dari Arduino
#[derive(Debug, Clone)]
pub struct UnifiedSensorRaw {
    pub no2: f32,
    pub eth: f32,
    pub voc: f32,
    pub co: f32,
    pub com: f32,
    pub ethm: f32,
    pub vocm: f32,
    pub state: i32,
    pub level: i32,
}

// Hasil filter moving average
#[derive(Debug, Clone)]
pub struct UnifiedSensorFiltered {
    pub no2: f32,
    pub eth: f32,
    pub voc: f32,
    pub co: f32,
    pub com: f32,
    pub ethm: f32,
    pub vocm: f32,
    pub state: i32,
    pub level: i32,
}

// ================= SensorFilters =================
#[derive(Clone)]
pub struct SensorFilters {
    window_size: usize,
    no2: Vec<f32>,
    eth: Vec<f32>,
    voc: Vec<f32>,
    co: Vec<f32>,
    com: Vec<f32>,
    ethm: Vec<f32>,
    vocm: Vec<f32>,
    // Sinusoidal modulation parameters
    sine_amplitude: f32,
    sine_frequency: f32,
    sine_enabled: bool,
    start_time: SystemTime,
}

impl SensorFilters {
    pub fn new(config: &FilterConfig) -> Self {
        Self {
            window_size: config.window_size,
            no2: Vec::new(),
            eth: Vec::new(),
            voc: Vec::new(),
            co: Vec::new(),
            com: Vec::new(),
            ethm: Vec::new(),
            vocm: Vec::new(),
            sine_amplitude: config.sine_amplitude,
            sine_frequency: config.sine_frequency,
            sine_enabled: config.sine_enabled,
            start_time: SystemTime::now(),
        }
    }

    fn moving_average(values: &mut Vec<f32>, new_val: f32, window_size: usize) -> f32 {
        values.push(new_val);
        if values.len() > window_size {
            values.remove(0);
        }
        let sum: f32 = values.iter().sum();
        sum / values.len() as f32
    }

    /// Apply sinusoidal modulation: output = input × (1 + A × sin(2πft))
    fn apply_sine_modulation(&self, value: f32) -> f32 {
        if !self.sine_enabled {
            return value;
        }

        // Calculate elapsed time in seconds
        let elapsed = self.start_time.elapsed().unwrap_or_default();
        let t = elapsed.as_secs_f32();

        // Calculate sine wave: sin(2πft)
        let angle = 2.0 * std::f32::consts::PI * self.sine_frequency * t;
        let sine_value = angle.sin();

        // Apply modulation: output = input × (1 + A × sin(2πft))
        value * (1.0 + self.sine_amplitude * sine_value)
    }

    pub fn update(&mut self, raw: &UnifiedSensorRaw) -> UnifiedSensorFiltered {
        // Apply moving average first
        let no2_avg = Self::moving_average(&mut self.no2, raw.no2, self.window_size);
        let eth_avg = Self::moving_average(&mut self.eth, raw.eth, self.window_size);
        let voc_avg = Self::moving_average(&mut self.voc, raw.voc, self.window_size);
        let co_avg = Self::moving_average(&mut self.co, raw.co, self.window_size);
        let com_avg = Self::moving_average(&mut self.com, raw.com, self.window_size);
        let ethm_avg = Self::moving_average(&mut self.ethm, raw.ethm, self.window_size);
        let vocm_avg = Self::moving_average(&mut self.vocm, raw.vocm, self.window_size);

        // Then apply sinusoidal modulation
        UnifiedSensorFiltered {
            no2: self.apply_sine_modulation(no2_avg),
            eth: self.apply_sine_modulation(eth_avg),
            voc: self.apply_sine_modulation(voc_avg),
            co: self.apply_sine_modulation(co_avg),
            com: self.apply_sine_modulation(com_avg),
            ethm: self.apply_sine_modulation(ethm_avg),
            vocm: self.apply_sine_modulation(vocm_avg),
            state: raw.state,
            level: raw.level,
        }
    }
}
