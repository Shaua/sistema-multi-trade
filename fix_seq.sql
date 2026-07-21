SELECT setval('accounts_id_seq', COALESCE((SELECT MAX(id)+1 FROM accounts), 1), false);
SELECT setval('trades_id_seq', COALESCE((SELECT MAX(id)+1 FROM trades), 1), false);
SELECT setval('signals_id_seq', COALESCE((SELECT MAX(id)+1 FROM signals), 1), false);
SELECT setval('candle_data_id_seq', COALESCE((SELECT MAX(id)+1 FROM candle_data), 1), false);
SELECT setval('system_settings_id_seq', COALESCE((SELECT MAX(id)+1 FROM system_settings), 1), false);
