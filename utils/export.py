import pandas as pd
import io
from datetime import datetime

def export_to_excel(df):
    """Экспортирует данные в Excel"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Currency Rates', index=False)
        
        # Добавляем метаданные
        workbook = writer.book
        worksheet = writer.sheets['Currency Rates']
        worksheet.cell(row=1, column=len(df.columns)+2, value=f"Экспортировано: {datetime.now()}")
    
    return output.getvalue()

def export_to_csv(df):
    """Экспортирует данные в CSV"""
    return df.to_csv(index=False).encode('utf-8')

def export_to_json(df):
    """Экспортирует данные в JSON"""
    return df.to_json(orient='records', force_ascii=False).encode('utf-8')