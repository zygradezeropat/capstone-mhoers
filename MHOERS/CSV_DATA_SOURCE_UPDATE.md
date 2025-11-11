# CSV Data Source Update - Disease Peak Analytics

## ✅ What Changed

The `predict_disease_peaks_2025` command now **loads data from CSV files by default** instead of querying the Django database.

## 📁 CSV File Locations

The script automatically looks for CSV files at:
- **2023 Data**: `MHOERS/sample_datasets/New_Corella_datasets_2023.csv`
- **2024 Data**: `MHOERS/sample_datasets/New_corella_datasets_5.csv`

## 🚀 Usage

### **Default: Use CSV Files**
```bash
python manage.py predict_disease_peaks_2025
```
This will automatically load from the CSV files in `sample_datasets/` folder.

### **Use Django Database Instead**
```bash
python manage.py predict_disease_peaks_2025 --use-db
```
This loads data from your Django `Referral` and `Patient` models.

### **Custom CSV File Paths**
```bash
python manage.py predict_disease_peaks_2025 \
    --csv-2023 /path/to/2023_data.csv \
    --csv-2024 /path/to/2024_data.csv
```

### **All Options Combined**
```bash
python manage.py predict_disease_peaks_2025 \
    --top-n 10 \
    --samples-per-month 200 \
    --csv-2023 custom_2023.csv \
    --csv-2024 custom_2024.csv
```

## 📊 CSV File Format

The CSV files should have these columns:
- `AGE` - Patient age (numeric)
- `SEX` - Patient sex (Male/Female)
- `COMPLAINTS` - Chief complaint or symptoms (text)
- `DIAGNOSIS` - Diagnosis text (text)
- `ICD10 CODE` - ICD10 diagnosis code (e.g., T14.1, J06.9)

**Note:** The script handles:
- Missing ICD10 codes (extracts from diagnosis text if available)
- Case-insensitive column names
- Extra columns (only uses required ones)

## 🔄 How It Works

### **CSV Mode (Default)**
1. Loads `New_Corella_datasets_2023.csv` and `New_corella_datasets_5.csv`
2. Combines both files into one DataFrame
3. Standardizes column names
4. Extracts ICD10 codes from diagnosis text if missing
5. Processes data through ML pipeline

### **Database Mode (`--use-db`)**
1. Queries `Referral` objects from 2023-2024
2. Joins with `Patient` data
3. Maps Django model fields to DataFrame columns
4. Uses `ICD_code` field if available
5. Processes data through ML pipeline

## 📋 CSV Column Mapping

| CSV Column | Used For |
|------------|----------|
| `AGE` | Feature (patient age) |
| `SEX` | Feature (patient sex) |
| `COMPLAINTS` | Feature (chief complaint) |
| `DIAGNOSIS` | Feature (diagnosis text) |
| `ICD10 CODE` | Target (disease to predict) |

## 🎯 Benefits of CSV Mode

1. **Faster**: No database queries needed
2. **Portable**: Works with exported data
3. **Flexible**: Easy to test with different datasets
4. **Offline**: Can run without database connection

## 🔍 Data Processing

The script automatically:
- ✅ Handles missing ICD10 codes (extracts from diagnosis)
- ✅ Cleans empty values
- ✅ Standardizes column names
- ✅ Combines 2023 and 2024 data
- ✅ Filters to top N diseases
- ✅ Encodes categorical data for ML

## 📝 Example Output

```
📂 Loading CSV files...
   2023: C:\...\MHOERS\sample_datasets\New_Corella_datasets_2023.csv
   2024: C:\...\MHOERS\sample_datasets\New_corella_datasets_5.csv
   ✅ Loaded 2023: 2533 records
   ✅ Loaded 2024: 4800 records
✅ Loaded 7333 total records from CSV files

🔍 Identifying top 5 diseases...
Top 5 ICD10 codes found: ['T14.1', 'W54.99', 'J06.9', 'Z00', 'I10.1']
✅ Filtered to 4500 records with top diseases
...
```

## ⚠️ Troubleshooting

### **File Not Found Error**
```
❌ File not found: sample_datasets/New_Corella_datasets_2023.csv
```

**Solution:** 
- Check that CSV files are in `MHOERS/sample_datasets/` folder
- Or specify custom paths with `--csv-2023` and `--csv-2024`

### **Missing Columns**
```
⚠️  Column "ICD10 CODE" not found in CSV
```

**Solution:**
- Ensure CSV has required columns (case-insensitive matching works)
- Or use `--use-db` to load from database instead

### **Empty ICD10 Codes**
The script automatically extracts ICD10 codes from diagnosis text if the `ICD10 CODE` column is empty.

## 🔄 Switching Between Modes

You can easily switch between CSV and database modes:

```bash
# Use CSV (default)
python manage.py predict_disease_peaks_2025

# Use database
python manage.py predict_disease_peaks_2025 --use-db
```

Both modes produce the same output format and use the same ML pipeline!









