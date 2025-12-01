"""
E-Nose Utilities - Edge Impulse Handler
"""

import csv
import json
import requests
from typing import Optional, Dict, Any
from edge_impulse_linux.runner import ImpulseRunner


class EdgeImpulseHandler:
    """Handler untuk Edge Impulse model loading dan classification"""
    
    def __init__(self, model_path: str = None):
        self.runner = None
        self.model_path = model_path
        self.initialized = False
        self.model_info = None
        
        if model_path:
            self.load_model(model_path)

    def load_model(self, model_path: str) -> bool:
        """
        Load Edge Impulse model dari file .eim
        
        Args:
            model_path: Path ke file model .eim
            
        Returns:
            True jika berhasil load, False jika gagal
        """
        try:
            if self.runner:
                try:
                    self.runner.stop()
                except:
                    pass
            
            self.runner = ImpulseRunner(model_path)
            self.model_path = model_path
            self.model_info = self.runner.init()
            print(f"✅ Edge Impulse model loaded: {self.model_info}")
            self.initialized = True
            return True
        except Exception as e:
            print(f"❌ Failed to load Edge Impulse model: {e}")
            self.initialized = False
            return False

    def classify(self, data: dict) -> dict:
        """
        Classify sensor data menggunakan Edge Impulse model
        
        Args:
            data: Dictionary berisi sensor readings (NO2, ETH, VOC, dll)
            
        Returns:
            Classification result atau None jika gagal
        """
        if not self.initialized:
            return None

        # Mapping sensor data to features expected by the model
        features = []
        try:
            # Order: NO2, ETH, VOC, CO, COM, ETHM, VOCM
            feature_keys = ["NO2", "ETH", "VOC", "CO", "COM", "ETHM", "VOCM"]
            for key in feature_keys:
                if key in data:
                    features.append(float(data[key]))
                else:
                    return None  # Missing data for classification
            
            res = self.runner.classify(features)
            return res["result"]
        except Exception as e:
            print(f"❌ Classification error: {e}")
            return None

    @staticmethod
    def upload_csv_to_edge_impulse(
        csv_file_path: str,
        api_key: str,
        project_id: str,
        label: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Upload CSV file to Edge Impulse for training data ingestion
        
        Args:
            csv_file_path: Path to the CSV file to upload
            api_key: Edge Impulse API key
            project_id: Edge Impulse project ID
            label: Label for the data (default: "unknown")
            
        Returns:
            Dictionary with 'success' (bool) and 'message' (str) keys
        """
        try:
            # Read CSV file
            with open(csv_file_path, 'r') as f:
                csv_reader = csv.DictReader(f)
                rows = list(csv_reader)
            
            if not rows:
                return {
                    'success': False,
                    'message': 'CSV file is empty'
                }
            
            # Prepare data for Edge Impulse
            # Edge Impulse expects JSON format with structured data
            samples = []
            for row in rows:
                sample = {
                    'timestamp': row.get('timestamp', ''),
                    'values': {
                        'NO2': float(row.get('NO2', 0)),
                        'ETH': float(row.get('ETH', 0)),
                        'VOC': float(row.get('VOC', 0)),
                        'CO': float(row.get('CO', 0)),
                        'COM': float(row.get('COM', 0)),
                        'ETHM': float(row.get('ETHM', 0)),
                        'VOCM': float(row.get('VOCM', 0))
                    }
                }
                samples.append(sample)
            
            # Prepare payload
            payload = {
                'protected': False,
                'label': label,
                'samples': samples
            }
            
            # API endpoint
            url = f"https://ingestion.edgeimpulse.com/api/training/data"
            
            # Headers with authentication
            headers = {
                'x-api-key': api_key,
                'x-project-id': project_id,
                'Content-Type': 'application/json'
            }
            
            # Send request
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200 or response.status_code == 201:
                return {
                    'success': True,
                    'message': f'Successfully uploaded {len(samples)} samples to Edge Impulse'
                }
            else:
                return {
                    'success': False,
                    'message': f'Upload failed: {response.status_code} - {response.text}'
                }
                
        except FileNotFoundError:
            return {
                'success': False,
                'message': f'CSV file not found: {csv_file_path}'
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'message': f'Network error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error uploading to Edge Impulse: {str(e)}'
            }

    @staticmethod
    def upload_data_to_edge_impulse(
        data: list,
        api_key: str,
        project_id: str,
        label: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Upload data directly to Edge Impulse (without CSV file) for real-time integration
        
        Args:
            data: List of dictionaries with sensor data (from current_sample_data)
            api_key: Edge Impulse API key
            project_id: Edge Impulse project ID
            label: Label for the data (default: "unknown")
            
        Returns:
            Dictionary with 'success' (bool) and 'message' (str) keys
        """
        try:
            if not data:
                return {
                    'success': False,
                    'message': 'No data to upload'
                }
            
            # Prepare data for Edge Impulse
            samples = []
            for row in data:
                sample = {
                    'timestamp': row.get('timestamp', ''),
                    'values': {
                        'NO2': float(row.get('NO2', 0)),
                        'ETH': float(row.get('ETH', 0)),
                        'VOC': float(row.get('VOC', 0)),
                        'CO': float(row.get('CO', 0)),
                        'COM': float(row.get('COM', 0)),
                        'ETHM': float(row.get('ETHM', 0)),
                        'VOCM': float(row.get('VOCM', 0))
                    }
                }
                samples.append(sample)
            
            # Prepare payload
            payload = {
                'protected': False,
                'label': label,
                'samples': samples
            }
            
            # API endpoint
            url = "https://ingestion.edgeimpulse.com/api/training/data"
            
            # Headers with authentication
            headers = {
                'x-api-key': api_key,
                'x-project-id': project_id,
                'Content-Type': 'application/json'
            }
            
            # Send request
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200 or response.status_code == 201:
                return {
                    'success': True,
                    'message': f'Successfully uploaded {len(samples)} samples to Edge Impulse'
                }
            else:
                return {
                    'success': False,
                    'message': f'Upload failed: {response.status_code} - {response.text}'
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'message': f'Network error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error uploading to Edge Impulse: {str(e)}'
            }
