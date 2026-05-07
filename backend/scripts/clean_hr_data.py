import pandas as pd
import os

csv_path = r"c:\Users\anure\Desktop\enterprise_rag\storage\documents\raw\hr_data.csv"

if not os.path.exists(csv_path):
    print(f"Error: {csv_path} not found.")
else:
    df = pd.read_csv(csv_path)
    initial_count = len(df)
    
    # Deduplicate by employee_id and email to ensure distinct employees are preserved
    df_cleaned = df.drop_duplicates(subset=["employee_id", "email"], keep="first")
    
    final_count = len(df_cleaned)
    print(f"Initial rows: {initial_count}")
    print(f"Final rows: {final_count}")
    print(f"Removed {initial_count - final_count} duplicates.")
    
    df_cleaned.to_csv(csv_path, index=False)
    print("Cleaned CSV saved.")
