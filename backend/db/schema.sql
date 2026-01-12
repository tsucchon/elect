-- 発電量実績
CREATE TABLE generation_actual (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    area TEXT NOT NULL,           -- 'tokyo'
    timestamp DATETIME NOT NULL,  -- 30分単位
    pv_mw REAL,                   -- 太陽光発電量 (MW)
    wind_mw REAL,                 -- 風力発電量 (MW)
    total_mw REAL,                -- PV+Wind合計
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_generation_area_time ON generation_actual(area, timestamp);

-- 価格実績
CREATE TABLE price_actual (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    area TEXT NOT NULL,
    timestamp DATETIME NOT NULL,  -- 30分単位
    price_yen REAL NOT NULL,      -- スポット価格 (円/kWh)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_price_area_time ON price_actual(area, timestamp);

-- 予測結果
CREATE TABLE predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    area TEXT NOT NULL,
    target_type TEXT NOT NULL,     -- 'generation' or 'price'
    forecast_timestamp DATETIME NOT NULL,  -- 予測対象時刻
    predicted_value REAL NOT NULL,
    actual_value REAL,             -- 実績が入ったら更新
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_predictions_area_type_time ON predictions(area, target_type, forecast_timestamp);

-- 気象予報データ
CREATE TABLE weather_forecast (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    area TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    solar_radiation REAL,          -- W/m²
    wind_speed REAL,               -- m/s
    temperature REAL,              -- ℃
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_weather_area_time ON weather_forecast(area, timestamp);
