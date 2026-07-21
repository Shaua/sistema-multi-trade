from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://neondb_owner:npg_jBWsTLqf5hF9@ep-tiny-dust-advv3wz2.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require"
engine = create_engine(DATABASE_URL)

def main():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT active_assets FROM system_settings LIMIT 1;"))
        row = result.fetchone()
        if row:
            current_assets = row[0]
            print(f"Current assets: {current_assets}")
            assets_list = current_assets.split(',')
            to_remove = ['MATIC/USDT', 'ICP/USDT', 'RNDR/USDT', 'MKR/USDT']
            new_assets = [a for a in assets_list if a not in to_remove]
            new_assets_str = ','.join(new_assets)
            print(f"New assets: {new_assets_str}")
            conn.execute(text("UPDATE system_settings SET active_assets = :new_assets"), {"new_assets": new_assets_str})
            conn.commit()
            print("Assets updated successfully.")
        else:
            print("No system settings found.")

if __name__ == "__main__":
    main()
