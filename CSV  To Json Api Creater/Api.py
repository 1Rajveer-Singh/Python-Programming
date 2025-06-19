import sys
import json
import csv
import os
import re
import threading
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
import pandas as pd
import numpy as np
from flask import Flask, jsonify, request
from flask_cors import CORS
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QPushButton, QLabel, QFileDialog, QTextEdit, 
                             QProgressBar, QMessageBox, QCheckBox, QLineEdit, 
                             QGroupBox, QGridLayout, QSpinBox, QTabWidget, QTableWidget,
                             QTableWidgetItem, QHeaderView, QSplitter)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QTextCursor
import warnings
warnings.filterwarnings('ignore')


class DataProcessor(QThread):
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    finished_processing = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    preview_ready = pyqtSignal(list, list)
    
    def __init__(self, file_path, config):
        super().__init__()
        self.file_path = file_path
        self.config = config
        self.df = None
        
    def run(self):
        try:
            self.status_updated.emit("Starting file processing...")
            self.progress_updated.emit(5)
            
            # Load file based on extension
            file_ext = os.path.splitext(self.file_path)[1].lower()
            
            if file_ext == '.csv':
                self.df = self.load_csv_file()
            elif file_ext in ['.xlsx', '.xls']:
                self.df = self.load_excel_file()
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")
            
            self.progress_updated.emit(30)
            self.status_updated.emit("Processing data...")
            
            # Clean and process data
            self.clean_data()
            self.progress_updated.emit(60)
            
            # Generate preview
            headers = list(self.df.columns)
            preview_data = []
            for _, row in self.df.head(10).iterrows():
                preview_data.append([str(val) if pd.notna(val) else "" for val in row])
            
            self.preview_ready.emit(headers, preview_data)
            self.progress_updated.emit(80)
            
            # Generate JSON API
            api_data = self.generate_json_api()
            self.progress_updated.emit(100)
            
            self.status_updated.emit("Processing completed successfully!")
            self.finished_processing.emit(api_data)
            
        except Exception as e:
            self.error_occurred.emit(f"Error processing file: {str(e)}")
    
    def load_csv_file(self):
        """Load CSV file with intelligent delimiter detection and error handling"""
        try:
            self.status_updated.emit("Analyzing CSV structure...")
            
            # Try different encodings
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
            df = None
            
            for encoding in encodings:
                try:
                    # First, try to detect delimiter
                    with open(self.file_path, 'r', encoding=encoding) as file:
                        sample = file.read(4096)
                        
                    # Try different delimiters
                    delimiters = [',', ';', '\t', '|', ':', ' ']
                    best_delimiter = ','
                    max_columns = 0
                    
                    for delimiter in delimiters:
                        try:
                            test_df = pd.read_csv(self.file_path, delimiter=delimiter, 
                                                encoding=encoding, nrows=5)
                            if len(test_df.columns) > max_columns:
                                max_columns = len(test_df.columns)
                                best_delimiter = delimiter
                        except:
                            continue
                    
                    # Load full file with best delimiter
                    df = pd.read_csv(self.file_path, delimiter=best_delimiter, 
                                   encoding=encoding, low_memory=False)
                    
                    # If only one column, try fixed-width parsing
                    if len(df.columns) == 1:
                        try:
                            df = pd.read_fwf(self.file_path, encoding=encoding)
                        except:
                            pass
                    
                    self.status_updated.emit(f"CSV loaded with {encoding} encoding and '{best_delimiter}' delimiter")
                    break
                    
                except Exception as e:
                    continue
            
            if df is None:
                raise ValueError("Could not parse CSV file with any supported encoding or delimiter")
            
            return df
            
        except Exception as e:
            raise Exception(f"CSV loading error: {str(e)}")
    
    def load_excel_file(self):
        """Load Excel file with comprehensive error handling"""
        try:
            self.status_updated.emit("Loading Excel file...")
            
            # Try to read Excel file
            try:
                # First try default sheet
                df = pd.read_excel(self.file_path, engine='openpyxl')
            except:
                try:
                    # Try with xlrd engine for older files
                    df = pd.read_excel(self.file_path, engine='xlrd')
                except:
                    # Try reading all sheets and use the first non-empty one
                    excel_file = pd.ExcelFile(self.file_path)
                    df = None
                    for sheet_name in excel_file.sheet_names:
                        try:
                            temp_df = pd.read_excel(self.file_path, sheet_name=sheet_name)
                            if not temp_df.empty:
                                df = temp_df
                                self.status_updated.emit(f"Using sheet: {sheet_name}")
                                break
                        except:
                            continue
                    
                    if df is None:
                        raise ValueError("No readable sheets found in Excel file")
            
            return df
            
        except Exception as e:
            raise Exception(f"Excel loading error: {str(e)}")
    
    def clean_data(self):
        """Clean and standardize data"""
        try:
            self.status_updated.emit("Cleaning data...")
            
            # Clean column names
            self.df.columns = [self.clean_column_name(col) for col in self.df.columns]
            
            # Remove completely empty rows and columns
            self.df = self.df.dropna(how='all').dropna(axis=1, how='all')
            
            # Convert data types intelligently
            for col in self.df.columns:
                self.df[col] = self.df[col].apply(self.smart_convert_value)
            
            self.status_updated.emit(f"Data cleaned: {len(self.df)} rows, {len(self.df.columns)} columns")
            
        except Exception as e:
            raise Exception(f"Data cleaning error: {str(e)}")
    
    def clean_column_name(self, name):
        """Clean column names for API compatibility"""
        # Convert to string and strip whitespace
        name = str(name).strip()
        
        # Replace spaces and special characters with underscores
        name = re.sub(r'[^\w]', '_', name)
        
        # Remove multiple consecutive underscores
        name = re.sub(r'_+', '_', name)
        
        # Remove leading/trailing underscores
        name = name.strip('_')
        
        # Ensure it doesn't start with a number
        if name and name[0].isdigit():
            name = 'col_' + name
        
        # Handle empty names
        if not name:
            name = 'unnamed_column'
        
        return name.lower()
    
    def smart_convert_value(self, value):
        """Intelligently convert values to appropriate types"""
        if pd.isna(value):
            return None
        
        # Convert to string first
        str_value = str(value).strip()
        
        if not str_value:
            return None
        
        # Boolean conversion
        if str_value.lower() in ['true', 'yes', '1', 'on', 'y']:
            return True
        elif str_value.lower() in ['false', 'no', '0', 'off', 'n']:
            return False
        
        # Numeric conversion
        try:
            # Try integer first
            if '.' not in str_value and 'e' not in str_value.lower():
                return int(float(str_value))
            else:
                return float(str_value)
        except (ValueError, OverflowError):
            pass
        
        # Date conversion attempts
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
            r'\d{2}-\d{2}-\d{4}',  # MM-DD-YYYY
        ]
        
        for pattern in date_patterns:
            if re.match(pattern, str_value):
                try:
                    pd.to_datetime(str_value)
                    return str_value  # Keep as string for JSON compatibility
                except:
                    pass
        
        return str_value
    
    def generate_json_api(self):
        """Generate comprehensive JSON API structure"""
        try:
            self.status_updated.emit("Generating JSON API...")
            
            # Convert DataFrame to records
            records = self.df.to_dict('records')
            
            # Generate field information
            fields_info = {}
            for col in self.df.columns:
                sample_values = self.df[col].dropna().head(5).tolist()
                data_types = list(set([type(val).__name__ for val in sample_values if val is not None]))
                
                fields_info[col] = {
                    "type": data_types[0] if len(data_types) == 1 else "mixed",
                    "sample_values": sample_values[:3],
                    "null_count": int(self.df[col].isna().sum()),
                    "unique_count": int(self.df[col].nunique())
                }
            
            # Generate API structure
            api_structure = {
                "api_info": {
                    "version": "1.0",
                    "title": f"{os.path.splitext(os.path.basename(self.file_path))[0]} API",
                    "description": f"Generated JSON API from {os.path.splitext(self.file_path)[1]} file",
                    "generated_at": datetime.now().isoformat(),
                    "source_file": os.path.basename(self.file_path)
                },
                "metadata": {
                    "total_records": len(records),
                    "total_fields": len(self.df.columns),
                    "fields": list(self.df.columns),
                    "fields_info": fields_info,
                    "data_quality": {
                        "empty_rows_removed": 0,  # Could track this
                        "duplicate_rows": int(self.df.duplicated().sum()),
                        "completeness_score": round((1 - self.df.isna().sum().sum() / (len(self.df) * len(self.df.columns))) * 100, 2)
                    }
                },
                "endpoints": {
                    "get_all": "/api/data",
                    "get_by_id": "/api/data/{id}",
                    "search": "/api/data/search?q={query}",
                    "filter": "/api/data/filter?field={field}&value={value}",
                    "paginate": "/api/data?page={page}&limit={limit}",
                    "fields": "/api/fields",
                    "stats": "/api/stats"
                },
                "data": records[:self.config.get('preview_limit', 1000)] if self.config.get('preview_only', False) else records
            }
            
            return api_structure
            
        except Exception as e:
            raise Exception(f"JSON API generation error: {str(e)}")


class FlaskAPIServer:
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for React frontend
        self.api_data = None
        self.setup_routes()
        
    def setup_routes(self):
        @self.app.route('/api/status', methods=['GET'])
        def health_check():
            """Health check endpoint for React app"""
            return jsonify({
                "status": "healthy",
                "data_loaded": self.api_data is not None,
                "timestamp": datetime.now().isoformat()
            })
        
        @self.app.route('/api/data', methods=['GET'])
        def get_all_data():
            if not self.api_data:
                return jsonify({"error": "No data loaded"}), 404
            
            try:
                page = request.args.get('page', 1, type=int)
                limit = request.args.get('limit', 100, type=int)
                
                data = self.api_data.get('data', [])
                start = (page - 1) * limit
                end = start + limit
                
                return jsonify({
                    "success": True,
                    "data": data[start:end],
                    "pagination": {
                        "page": page,
                        "limit": limit,
                        "total": len(data),
                        "pages": (len(data) + limit - 1) // limit,
                        "has_next": end < len(data),
                        "has_prev": page > 1
                    },
                    "metadata": self.api_data.get('metadata', {})
                })
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500
        
        @self.app.route('/api/data/<int:record_id>', methods=['GET'])
        def get_by_id(record_id):
            if not self.api_data:
                return jsonify({"success": False, "error": "No data loaded"}), 404
            
            try:
                data = self.api_data.get('data', [])
                if 0 <= record_id < len(data):
                    return jsonify({
                        "success": True,
                        "data": data[record_id],
                        "id": record_id
                    })
                else:
                    return jsonify({"success": False, "error": "Record not found"}), 404
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500
        
        @self.app.route('/api/data/search', methods=['GET'])
        def search_data():
            if not self.api_data:
                return jsonify({"success": False, "error": "No data loaded"}), 404
            
            try:
                query = request.args.get('q', '').lower()
                if not query:
                    return jsonify({"success": False, "error": "Query parameter 'q' is required"}), 400
                
                data = self.api_data.get('data', [])
                results = []
                
                for idx, record in enumerate(data):
                    for value in record.values():
                        if value and query in str(value).lower():
                            results.append({**record, "_id": idx})
                            break
                
                return jsonify({
                    "success": True,
                    "query": query,
                    "results": results,
                    "count": len(results)
                })
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500
        
        @self.app.route('/api/fields', methods=['GET'])
        def get_fields():
            """Return fields info compatible with React CSV context"""
            if not self.api_data:
                return jsonify({"success": False, "error": "No data loaded"}), 404
            
            try:
                metadata = self.api_data.get('metadata', {})
                fields_info = metadata.get('fields_info', {})
                
                # Format for React compatibility
                formatted_fields = {}
                for field_name, field_data in fields_info.items():
                    formatted_fields[field_name] = {
                        "name": field_name,
                        "type": field_data.get('type', 'string'),
                        "sample_values": field_data.get('sample_values', []),
                        "null_count": field_data.get('null_count', 0),
                        "unique_count": field_data.get('unique_count', 0),
                        "description": f"{field_data.get('type', 'string')} field with {field_data.get('unique_count', 0)} unique values"
                    }
                
                return jsonify({
                    "success": True,
                    "fields": formatted_fields,
                    "field_names": list(formatted_fields.keys()),
                    "total_fields": len(formatted_fields),
                    "metadata": {
                        "total_records": metadata.get('total_records', 0),
                        "data_quality": metadata.get('data_quality', {}),
                        "source_file": self.api_data.get('api_info', {}).get('source_file', 'unknown')
                    }
                })
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500
        
        @self.app.route('/api/stats', methods=['GET'])
        def get_stats():
            if not self.api_data:
                return jsonify({"success": False, "error": "No data loaded"}), 404
            
            try:
                metadata = self.api_data.get('metadata', {})
                api_info = self.api_data.get('api_info', {})
                
                return jsonify({
                    "success": True,
                    "statistics": {
                        "total_records": metadata.get('total_records', 0),
                        "total_fields": metadata.get('total_fields', 0),
                        "data_quality": metadata.get('data_quality', {}),
                        "generated_at": api_info.get('generated_at'),
                        "source_file": api_info.get('source_file'),
                        "api_version": api_info.get('version', '1.0')
                    },
                    "fields_summary": metadata.get('fields_info', {})
                })
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500
        
        @self.app.route('/api/csv-format', methods=['GET'])
        def get_csv_format():
            """Return data in CSV-like format for React CSV context compatibility"""
            if not self.api_data:
                return jsonify({"success": False, "error": "No data loaded"}), 404
            
            try:
                data = self.api_data.get('data', [])
                if not data:
                    return jsonify({"success": False, "error": "No data available"}), 404
                
                # Get headers from first record
                headers = list(data[0].keys()) if data else []
                
                # Convert to CSV-like array format
                csv_array = [headers]  # First row is headers
                for record in data:
                    row = [str(record.get(header, '')) for header in headers]
                    csv_array.append(row)
                
                return jsonify({
                    "success": True,
                    "csv_data": csv_array,
                    "headers": headers,
                    "row_count": len(csv_array) - 1,  # Exclude header row
                    "col_count": len(headers)
                })
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500
        
        @self.app.route('/api/upload', methods=['POST'])
        def handle_csv_upload():
            """Handle CSV upload from React frontend as fallback"""
            try:
                if 'file' not in request.files:
                    return jsonify({"success": False, "error": "No file provided"}), 400
                
                file = request.files['file']
                if file.filename == '':
                    return jsonify({"success": False, "error": "No file selected"}), 400
                
                # Process uploaded CSV
                if file.filename.lower().endswith('.csv'):
                    # Read CSV data
                    csv_content = file.read().decode('utf-8')
                    lines = csv_content.strip().split('\n')
                    csv_data = [line.split(',') for line in lines]
                    
                    # Convert to API format
                    if len(csv_data) > 1:
                        headers = csv_data[0]
                        records = []
                        for row in csv_data[1:]:
                            record = {}
                            for i, header in enumerate(headers):
                                record[header.strip()] = row[i].strip() if i < len(row) else ''
                            records.append(record)
                        
                        # Create API structure
                        api_structure = {
                            "api_info": {
                                "version": "1.0",
                                "title": f"{file.filename} API",
                                "description": f"Uploaded CSV file with {len(records)} records",
                                "generated_at": datetime.now().isoformat(),
                                "source_file": file.filename
                            },
                            "metadata": {
                                "total_records": len(records),
                                "total_fields": len(headers),
                                "fields": headers,
                                "fields_info": {}
                            },
                            "data": records
                        }
                        
                        # Update server data
                        self.api_data = api_structure
                        
                        return jsonify({
                            "success": True,
                            "message": "File uploaded and processed successfully",
                            "records": len(records),
                            "fields": len(headers)
                        })
                    else:
                        return jsonify({"success": False, "error": "CSV file appears to be empty"}), 400
                else:
                    return jsonify({"success": False, "error": "Only CSV files are supported for upload"}), 400
                    
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500
    
    def update_data(self, api_data):
        self.api_data = api_data
    
    def start_server(self, port=5000):
        self.app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)


class DataToJSONAPIApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.file_path = None
        self.generated_api = None
        self.flask_server = FlaskAPIServer()
        self.server_thread = None
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("CSV/Excel to JSON API Generator")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("CSV/Excel to JSON API Generator")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin: 10px;")
        main_layout.addWidget(title)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Main processing tab
        self.setup_main_tab()
        
        # Preview tab
        self.setup_preview_tab()
        
        # Flask server tab
        self.setup_server_tab()
        
        # Status bar
        self.statusBar().showMessage("Ready - Select a CSV or Excel file to begin")
        
    def setup_main_tab(self):
        main_tab = QWidget()
        layout = QVBoxLayout(main_tab)
        
        # File selection
        file_group = QGroupBox("File Selection")
        file_layout = QHBoxLayout(file_group)
        
        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet("padding: 8px; border: 1px solid #bdc3c7; background: #ecf0f1; border-radius: 4px;")
        file_layout.addWidget(self.file_label)
        
        self.browse_btn = QPushButton("Browse File")
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        self.browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(self.browse_btn)
        
        layout.addWidget(file_group)
        
        # Configuration
        config_group = QGroupBox("Configuration")
        config_layout = QGridLayout(config_group)
        
        self.preview_checkbox = QCheckBox("Preview only (limit records)")
        config_layout.addWidget(self.preview_checkbox, 0, 0)
        
        config_layout.addWidget(QLabel("Record Limit:"), 0, 1)
        self.preview_limit = QSpinBox()
        self.preview_limit.setRange(10, 10000)
        self.preview_limit.setValue(1000)
        config_layout.addWidget(self.preview_limit, 0, 2)
        
        layout.addWidget(config_group)
        
        # Process button
        self.process_btn = QPushButton("Generate JSON API")
        self.process_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 12px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #229954; }
            QPushButton:disabled { background-color: #bdc3c7; }
        """)
        self.process_btn.clicked.connect(self.process_file)
        self.process_btn.setEnabled(False)
        layout.addWidget(self.process_btn)
        
        # Progress and status
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        layout.addWidget(self.status_label)
        
        # Output
        output_group = QGroupBox("Generated JSON API")
        output_layout = QVBoxLayout(output_group)
        
        self.output_text = QTextEdit()
        self.output_text.setFont(QFont("Consolas", 10))
        self.output_text.setReadOnly(True)
        output_layout.addWidget(self.output_text)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        self.copy_btn = QPushButton("Copy JSON")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        self.copy_btn.setEnabled(False)
        action_layout.addWidget(self.copy_btn)
        
        self.save_btn = QPushButton("Save JSON")
        self.save_btn.clicked.connect(self.save_json)
        self.save_btn.setEnabled(False)
        action_layout.addWidget(self.save_btn)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_output)
        action_layout.addWidget(self.clear_btn)
        
        output_layout.addLayout(action_layout)
        layout.addWidget(output_group)
        
        self.tab_widget.addTab(main_tab, "Main")
        
    def setup_preview_tab(self):
        preview_tab = QWidget()
        layout = QVBoxLayout(preview_tab)
        
        layout.addWidget(QLabel("Data Preview (First 10 rows)"))
        
        self.preview_table = QTableWidget()
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.preview_table)
        
        self.tab_widget.addTab(preview_tab, "Preview")
        
    def setup_server_tab(self):
        server_tab = QWidget()
        layout = QVBoxLayout(server_tab)
        
        # Server controls
        server_group = QGroupBox("Flask API Server")
        server_layout = QGridLayout(server_group)
        
        server_layout.addWidget(QLabel("Port:"), 0, 0)
        self.port_input = QLineEdit("5000")
        server_layout.addWidget(self.port_input, 0, 1)
        
        self.start_server_btn = QPushButton("Start Server")
        self.start_server_btn.clicked.connect(self.start_flask_server)
        self.start_server_btn.setEnabled(False)
        server_layout.addWidget(self.start_server_btn, 0, 2)
        
        self.stop_server_btn = QPushButton("Stop Server")
        self.stop_server_btn.clicked.connect(self.stop_flask_server)
        self.stop_server_btn.setEnabled(False)
        server_layout.addWidget(self.stop_server_btn, 0, 3)
        
        layout.addWidget(server_group)
        
        # API endpoints info
        endpoints_group = QGroupBox("Available API Endpoints")
        endpoints_layout = QVBoxLayout(endpoints_group)
        
        self.endpoints_text = QTextEdit()
        self.endpoints_text.setReadOnly(True)
        self.endpoints_text.setMaximumHeight(200)
        endpoints_layout.addWidget(self.endpoints_text)
        
        layout.addWidget(endpoints_group)
        
        # Server logs
        logs_group = QGroupBox("Server Status")
        logs_layout = QVBoxLayout(logs_group)
        
        self.server_logs = QTextEdit()
        self.server_logs.setReadOnly(True)
        self.server_logs.setFont(QFont("Consolas", 9))
        logs_layout.addWidget(self.server_logs)
        
        layout.addWidget(logs_group)
        
        self.tab_widget.addTab(server_tab, "Flask Server")
        
    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV or Excel File",
            "",
            "Supported Files (*.csv *.xlsx *.xls);;CSV Files (*.csv);;Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        
        if file_path:
            self.file_path = file_path
            filename = os.path.basename(file_path)
            self.file_label.setText(filename)
            self.process_btn.setEnabled(True)
            self.statusBar().showMessage(f"File selected: {filename}")
            
    def process_file(self):
        if not self.file_path:
            return
        
        config = {
            'preview_only': self.preview_checkbox.isChecked(),
            'preview_limit': self.preview_limit.value()
        }
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.process_btn.setEnabled(False)
        self.status_label.setText("Starting processing...")
        
        # Start processing
        self.processor = DataProcessor(self.file_path, config)
        self.processor.progress_updated.connect(self.update_progress)
        self.processor.status_updated.connect(self.update_status)
        self.processor.preview_ready.connect(self.setup_preview_table)
        self.processor.finished_processing.connect(self.on_processing_finished)
        self.processor.error_occurred.connect(self.on_error)
        self.processor.start()
        
    def update_progress(self, value):
        self.progress_bar.setValue(value)
        
    def update_status(self, message):
        self.status_label.setText(message)
        self.statusBar().showMessage(message)
        
    def setup_preview_table(self, headers, data):
        self.preview_table.setColumnCount(len(headers))
        self.preview_table.setRowCount(len(data))
        self.preview_table.setHorizontalHeaderLabels(headers)
        
        for row_idx, row_data in enumerate(data):
            for col_idx, cell_data in enumerate(row_data):
                item = QTableWidgetItem(str(cell_data))
                self.preview_table.setItem(row_idx, col_idx, item)
                
    def on_processing_finished(self, api_data):
        self.generated_api = api_data
        
        # Display JSON
        json_text = json.dumps(api_data, indent=2, ensure_ascii=False)
        self.output_text.setPlainText(json_text)
        
        # Enable buttons
        self.copy_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.start_server_btn.setEnabled(True)
        self.process_btn.setEnabled(True)
        
        # Hide progress
        self.progress_bar.setVisible(False)
        
        # Update Flask server data
        self.flask_server.update_data(api_data)
        
        # Update endpoints display
        self.update_endpoints_display()
        
        # Success message
        record_count = api_data['metadata']['total_records']
        QMessageBox.information(self, "Success", 
                              f"JSON API generated successfully!\n"
                              f"Records: {record_count}\n"
                              f"Fields: {api_data['metadata']['total_fields']}")
        
    def on_error(self, error_message):
        self.progress_bar.setVisible(False)
        self.process_btn.setEnabled(True)
        self.status_label.setText("Error occurred")
        
        QMessageBox.critical(self, "Processing Error", 
                           f"An error occurred:\n\n{error_message}")
        
    def update_endpoints_display(self):
        if not self.generated_api:
            return
            
        port = self.port_input.text()
        base_url = f"http://127.0.0.1:{port}"
        
        endpoints_info = f"""Available API Endpoints:

Core Data Endpoints:
GET {base_url}/api/status - Health check and server status
GET {base_url}/api/data - Get all data (with pagination)
GET {base_url}/api/data/{{id}} - Get specific record by ID
GET {base_url}/api/data/search?q={{query}} - Search data
GET {base_url}/api/fields - Get field information (React compatible)
GET {base_url}/api/stats - Get data statistics
GET {base_url}/api/csv-format - Get data in CSV array format
POST {base_url}/api/upload - Upload CSV file as fallback

React Integration Examples:
fetch('{base_url}/api/fields')
fetch('{base_url}/api/data?page=1&limit=10')
fetch('{base_url}/api/data/search?q=example')

CORS enabled for React frontend development.
"""
        self.endpoints_text.setPlainText(endpoints_info)
        
    def start_flask_server(self):
        try:
            port = int(self.port_input.text())
            
            def run_server():
                self.flask_server.start_server(port)
            
            self.server_thread = threading.Thread(target=run_server, daemon=True)
            self.server_thread.start()
            
            self.start_server_btn.setEnabled(False)
            self.stop_server_btn.setEnabled(True)
            
            self.server_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Flask server starting on port {port}")
            self.server_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Server running at http://127.0.0.1:{port}")
            
            QMessageBox.information(self, "Server Started", 
                                  f"Flask API server is running on port {port}\n"
                                  f"Access your API at: http://127.0.0.1:{port}/api/data")
            
        except ValueError:
            QMessageBox.warning(self, "Invalid Port", "Please enter a valid port number")
        except Exception as e:
            QMessageBox.critical(self, "Server Error", f"Failed to start server: {str(e)}")
            
    def stop_flask_server(self):
        # Note: Flask development server doesn't have a clean shutdown method
        # In production, you'd use a proper WSGI server
        self.start_server_btn.setEnabled(True)
        self.stop_server_btn.setEnabled(False)
        self.server_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Server stop requested")
        
    def copy_to_clipboard(self):
        if self.generated_api:
            clipboard = QApplication.clipboard()
            json_text = json.dumps(self.generated_api, indent=2, ensure_ascii=False)
            clipboard.setText(json_text)
            QMessageBox.information(self, "Copied", "JSON API copied to clipboard!")
            
    def save_json(self):
        if not self.generated_api:
            return
            
        default_name = f"{os.path.splitext(os.path.basename(self.file_path))[0]}_api.json"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save JSON API",
            default_name,
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.generated_api, f, indent=2, ensure_ascii=False)
                QMessageBox.information(self, "Saved", f"JSON API saved to:\n{file_path}")
                self.statusBar().showMessage(f"JSON API saved to {os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save file:\n{str(e)}")
                
    def clear_output(self):
        self.output_text.clear()
        self.generated_api = None
        self.copy_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.start_server_btn.setEnabled(False)
        self.preview_table.clear()
        self.preview_table.setRowCount(0)
        self.preview_table.setColumnCount(0)
        self.statusBar().showMessage("Output cleared - Ready for new processing")
        
    def closeEvent(self, event):
        """Handle application close event"""
        if self.server_thread and self.server_thread.is_alive():
            reply = QMessageBox.question(self, 'Close Application', 
                                       'Flask server is running. Close anyway?',
                                       QMessageBox.Yes | QMessageBox.No, 
                                       QMessageBox.No)
            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Set application properties
    app.setApplicationName("CSV/Excel to JSON API Generator")
    app.setApplicationVersion("2.0")
    
    # Apply modern styling
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f8f9fa;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        QPushButton {
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:disabled {
            background-color: #e9ecef;
            color: #6c757d;
        }
        QLineEdit, QSpinBox {
            border: 1px solid #ced4da;
            border-radius: 4px;
            padding: 6px;
        }
        QTextEdit {
            border: 1px solid #ced4da;
            border-radius: 4px;
        }
        QTableWidget {
            border: 1px solid #ced4da;
            border-radius: 4px;
            alternate-background-color: #f8f9fa;
        }
        QTabWidget::pane {
            border: 1px solid #dee2e6;
            border-radius: 4px;
        }
        QTabBar::tab {
            background-color: #e9ecef;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        QTabBar::tab:selected {
            background-color: #ffffff;
        }
    """)
    
    try:
        window = DataToJSONAPIApp()
        window.show()
        
        sys.exit(app.exec_())
        
    except Exception as e:
        QMessageBox.critical(None, "Application Error", 
                           f"Failed to start application:\n{str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    # Check for required dependencies
    required_packages = ['pandas', 'numpy', 'flask', 'flask_cors', 'openpyxl']
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'flask_cors':
                __import__('flask_cors')
            else:
                __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("Missing required packages:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nInstall them using:")
        print(f"pip install {' '.join(missing_packages)}")
        sys.exit(1)
    
    main()
