#!/usr/bin/env python3
"""
Usage:
    python3 autograder.py [submission_directory]
    
Example:
    python3 autograder.py ./candidate-submission
    
If no directory is provided, uses current directory.
"""

import requests
import json
import time
import sys
import os
import subprocess
import signal
import jaydebeapi
import shutil
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8080"
API_PORT = 8080
H2_JAR_PATH = os.path.expanduser("~/.m2/repository/com/h2database/h2/2.1.214/h2-2.1.214.jar")
H2_JDBC_URL = "jdbc:h2:file:/tmp/legalqa;AUTO_SERVER=TRUE"
STORAGE_PATH = "/tmp/legal-qa-storage"
DB_PATH = "/tmp/legalqa"

# Test questions
TEST_QUESTIONS = [
    {
        "question": "What Executive Order did President Trump issue regarding citizenship?",
        "keywords": ["executive", "order", "trump", "citizenship"],
        "min_citations": 1,
        "points": 10
    },
    {
        "question": "What is a universal injunction and why is it controversial?",
        "keywords": ["universal", "injunction", "controversial"],
        "min_citations": 1,
        "points": 10
    },
    {
        "question": "Who are the plaintiffs in this Supreme Court case?",
        "keywords": ["plaintiffs", "supreme", "court"],
        "min_citations": 1,
        "points": 10
    },
    {
        "question": "What does the Fourteenth Amendment say about birthright citizenship?",
        "keywords": ["fourteenth", "amendment", "birthright", "citizenship"],
        "min_citations": 1,
        "points": 10
    },
    {
        "question": "What statute gives federal courts equity jurisdiction?",
        "keywords": ["statute", "federal", "courts", "equity", "jurisdiction"],
        "min_citations": 1,
        "points": 10
    }
]

class FullAutograder:
    def __init__(self, submission_dir):
        self.submission_dir = Path(submission_dir).resolve()
        self.api_process = None
        self.ingestor_process = None
        self.total_points = 0
        self.max_points = 100
        self.results = []
        self.doc_id = None
        self.java_home = None
        
    def detect_java_home(self):
        """Detect JAVA_HOME from environment or system"""
        if self.java_home:
            return self.java_home
            
        # Check if already set
        if 'JAVA_HOME' in os.environ:
            self.java_home = os.environ['JAVA_HOME']
            return self.java_home
            
        # Try /usr/libexec/java_home (Mac)
        try:
            java_home = subprocess.check_output(
                ['/usr/libexec/java_home'],
                stderr=subprocess.DEVNULL,
                text=True
            ).strip()
            self.java_home = java_home
            os.environ['JAVA_HOME'] = java_home
            return java_home
        except:
            pass
            
        # Try to extract from mvn -version
        try:
            mvn_output = subprocess.check_output(
                ['mvn', '-version'],
                stderr=subprocess.DEVNULL,
                text=True
            )
            for line in mvn_output.split('\n'):
                if 'runtime:' in line.lower():
                    parts = line.split('runtime:')
                    if len(parts) > 1:
                        java_home = parts[1].strip()
                        self.java_home = java_home
                        os.environ['JAVA_HOME'] = java_home
                        return java_home
        except:
            pass
            
        return None
        
    def print_header(self):
        print("=" * 70)
        print("SUPREME COURT Q&A RAG SYSTEM - FULLY AUTOMATED AUTOGRADER")
        print("=" * 70)
        print(f"Submission directory: {self.submission_dir}")
        print()
        
    def print_section(self, title):
        print(f"\n{'='*70}")
        print(f"{title}")
        print(f"{'='*70}\n")
        
    def cleanup(self):
        """Clean up processes and temporary files"""
        print("\nCleaning up...")
        
        # Stop API server
        if self.api_process:
            print("  Stopping API server...")
            try:
                self.api_process.terminate()
                self.api_process.wait(timeout=10)
            except:
                self.api_process.kill()
                
        # Kill any remaining Java processes on port 8080
        try:
            subprocess.run(["pkill", "-f", "spring-boot:run"], stderr=subprocess.DEVNULL)
        except:
            pass
            
        # Clean up database and storage
        print("  Cleaning up database and storage...")
        try:
            for file in Path("/tmp").glob("legalqa*"):
                file.unlink()
        except:
            pass
            
        if os.path.exists(STORAGE_PATH):
            shutil.rmtree(STORAGE_PATH, ignore_errors=True)
            
        print("  Cleanup complete")
        
    def check_submission_structure(self):
        """Verify submission has required structure"""
        self.print_section("STEP 0: Checking Submission Structure")
        
        required = {
            "api-server": self.submission_dir / "api-server",
            "pom.xml": self.submission_dir / "api-server" / "pom.xml",
            "ingestor": self.submission_dir / "ingestor",
            "sample-documents": self.submission_dir / "sample-documents"
        }
        
        missing = []
        for name, path in required.items():
            if path.exists():
                print(f"  ✓ Found: {name}")
            else:
                print(f"  ✗ Missing: {name}")
                missing.append(name)
                
        if missing:
            print(f"\n✗ Submission is missing required files/directories")
            print(f"  Missing: {', '.join(missing)}")
            return False
            
        print(f"\n✓ Submission structure is valid")
        return True
        
    def start_api_server(self):
        """Start the API server in background"""
        self.print_section("STEP 1: Starting API Server")
        
        api_dir = self.submission_dir / "api-server"
        
        print("  Compiling and starting server (this may take 30-60 seconds)...")
        
        try:
            # Start Maven in background
            self.api_process = subprocess.Popen(
                ["mvn", "spring-boot:run"],
                cwd=str(api_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for server to start (check health endpoint)
            max_wait = 120  # 2 minutes
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                try:
                    response = requests.get(f"{API_BASE_URL}/health", timeout=2)
                    if response.status_code == 200:
                        print(f"  ✓ API server started successfully")
                        print(f"    Time to start: {int(time.time() - start_time)}s")
                        return True
                except:
                    pass
                    
                time.sleep(2)
                print(".", end="", flush=True)
                
            print(f"\n  ✗ API server failed to start within {max_wait}s")
            return False
            
        except Exception as e:
            print(f"  ✗ Failed to start API server: {e}")
            return False
            
    def upload_and_process_document(self):
        """Upload and process a test document"""
        self.print_section("STEP 2: Uploading and Processing Test Document")
        
        # Find a sample document
        sample_docs = list((self.submission_dir / "sample-documents").glob("*.txt"))
        if not sample_docs:
            print("  ✗ No sample documents found")
            return False
            
        test_doc = sample_docs[0]
        file_size = test_doc.stat().st_size
        
        print(f"  Using document: {test_doc.name} ({file_size:,} bytes)")
        
        # Request upload
        try:
            response = requests.post(
                f"{API_BASE_URL}/upload/start",
                json={"filename": test_doc.name, "size": file_size},
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"  ✗ Upload request failed: {response.status_code}")
                return False
                
            data = response.json()
            self.doc_id = data.get("docId")
            upload_url = data.get("uploadUrl")
            
            if not self.doc_id or not upload_url:
                print(f"  ✗ Upload response missing docId or uploadUrl")
                return False
                
            print(f"  ✓ Upload request accepted")
            print(f"    Doc ID: {self.doc_id}")
            
        except Exception as e:
            print(f"  ✗ Upload request failed: {e}")
            return False
            
        # Copy file to storage
        try:
            os.makedirs(STORAGE_PATH, exist_ok=True)
            dest_file = Path(upload_url)
            shutil.copy(test_doc, dest_file)
            print(f"  ✓ File copied to storage")
        except Exception as e:
            print(f"  ✗ Failed to copy file: {e}")
            return False
            
        # Process with ingestor
        try:
            ingestor_script = self.submission_dir / "ingestor" / "ingestor_simple.py"
            
            if not ingestor_script.exists():
                print(f"  ✗ Ingestor script not found")
                return False
            
            # Install ingestor dependencies
            try:
                ingestor_dir = self.submission_dir / "ingestor"
                requirements_file = ingestor_dir / "requirements.txt"
                
                if requirements_file.exists():
                    print(f"  Installing ingestor dependencies...")
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", "-q", "-r", str(requirements_file)],
                        check=True,
                        timeout=120,
                        capture_output=True
                    )
                    print(f"  ✓ Dependencies installed")
                else:
                    # Install common dependencies if no requirements.txt
                    print(f"  Installing common dependencies...")
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", "-q", "jaydebeapi", "JPype1"],
                        check=True,
                        timeout=120,
                        capture_output=True
                    )
                    print(f"  ✓ Dependencies installed")
            except Exception as e:
                print(f"  ⚠ Warning: Could not install dependencies: {e}")
                
            print(f"  Processing document (this may take 10-30 seconds)...")
            
            # Detect JAVA_HOME
            java_home = self.detect_java_home()
            if java_home:
                print(f"    Using JAVA_HOME: {java_home}")
            else:
                print(f"    ⚠ Warning: Could not detect JAVA_HOME")
                print(f"    Please set JAVA_HOME environment variable")
            
            # Pass environment to subprocess
            env = os.environ.copy()
            
            result = subprocess.run(
                [sys.executable, str(ingestor_script), str(dest_file)],
                cwd=str(self.submission_dir / "ingestor"),
                capture_output=True,
                text=True,
                timeout=60,
                env=env
            )
            
            if result.returncode == 0:
                print(f"  ✓ Document processed successfully")
                # Print output for debugging
                for line in result.stdout.split('\n'):
                    if line.strip():
                        print(f"    {line}")
                return True
            else:
                print(f"  ✗ Ingestor failed")
                print(f"    Error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"  ✗ Ingestor timed out")
            return False
        except Exception as e:
            print(f"  ✗ Failed to run ingestor: {e}")
            return False
            
    def check_api_health(self):
        """Test: API Health Check (5 points)"""
        self.print_section("TEST 1: API Health Check")
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if response.status_code == 200 and response.text == "OK":
                points = 5
                self.total_points += points
                print(f"✓ API is healthy")
                print(f"  Points: {points}/5")
                self.results.append(("API Health", points, 5, "PASS"))
                return True
            else:
                print(f"✗ API returned unexpected response: {response.text}")
                self.results.append(("API Health", 0, 5, "FAIL"))
                return False
        except Exception as e:
            print(f"✗ Cannot connect to API: {e}")
            self.results.append(("API Health", 0, 5, "FAIL"))
            return False
            
    def check_upload_validation(self):
        """Test: File Upload Validation (15 points)"""
        self.print_section("TEST 2: File Upload Validation")
        points = 0
        
        # Test 2a: Valid file upload
        print("2a. Valid file upload (.txt, < 5MB)")
        try:
            response = requests.post(
                f"{API_BASE_URL}/upload/start",
                json={"filename": "test.txt", "size": 1000000},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if "uploadUrl" in data and "docId" in data:
                    points += 5
                    print(f"  ✓ Valid upload accepted")
                else:
                    print(f"  ✗ Response missing required fields")
            else:
                print(f"  ✗ Unexpected status code: {response.status_code}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            
        # Test 2b: Invalid file type
        print("\n2b. Invalid file type (.pdf)")
        try:
            response = requests.post(
                f"{API_BASE_URL}/upload/start",
                json={"filename": "test.pdf", "size": 1000000},
                timeout=5
            )
            if response.status_code == 400:
                points += 5
                print(f"  ✓ Invalid file type rejected")
            else:
                print(f"  ✗ Should return 400, got: {response.status_code}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            
        # Test 2c: File too large
        print("\n2c. File too large (> 5MB)")
        try:
            response = requests.post(
                f"{API_BASE_URL}/upload/start",
                json={"filename": "test.txt", "size": 10000000},
                timeout=5
            )
            if response.status_code == 400:
                points += 5
                print(f"  ✓ Large file rejected")
            else:
                print(f"  ✗ Should return 400, got: {response.status_code}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            
        self.total_points += points
        print(f"\n  Points: {points}/15")
        self.results.append(("Upload Validation", points, 15, "PASS" if points >= 10 else "PARTIAL"))
        
    def check_database_chunks(self):
        """Test: Document Processing & Chunking (20 points)"""
        self.print_section("TEST 3: Document Processing & Chunking")
        points = 0
        
        # Ensure JAVA_HOME is set for jaydebeapi
        java_home = self.detect_java_home()
        if not java_home:
            print(f"⚠ Warning: JAVA_HOME not set, database check may fail")
        
        try:
            conn = jaydebeapi.connect("org.h2.Driver", H2_JDBC_URL, ["sa", ""], H2_JAR_PATH)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM CHUNKS")
            chunk_count = cursor.fetchone()[0]
            
            print(f"Total chunks in database: {chunk_count}")
            
            if chunk_count > 0:
                points += 10
                print(f"✓ Chunks exist in database")
                
                # Check chunk structure
                cursor.execute("SELECT DOC_ID, CHUNK_ID, LENGTH(TEXT) FROM CHUNKS LIMIT 1")
                row = cursor.fetchone()
                if row and len(row) == 3:
                    points += 5
                    print(f"✓ Chunk structure is correct")
                    
                # Check chunk sizes
                cursor.execute("SELECT AVG(LENGTH(TEXT)) FROM CHUNKS")
                avg_length = cursor.fetchone()[0]
                if 600 <= avg_length <= 1000:
                    points += 5
                    print(f"✓ Chunk sizes are reasonable (avg: {int(avg_length)} chars)")
                else:
                    print(f"⚠ Chunk sizes may be off (avg: {int(avg_length)} chars)")
                    points += 2
                    
                # PRINT SAMPLE CHUNKS FOR DEBUGGING
                print(f"\nSample chunks from database:")
                cursor.execute("SELECT CHUNK_ID, SUBSTRING(TEXT, 1, 200) FROM CHUNKS LIMIT 3")
                for i, row in enumerate(cursor.fetchall(), 1):
                    chunk_id, text_sample = row
                    print(f"  Chunk {chunk_id}: {text_sample}...")
                    
            else:
                print(f"✗ No chunks found in database")
                
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"✗ Database check failed: {e}")
            
        self.total_points += points
        print(f"\n  Points: {points}/20")
        self.results.append(("Document Processing", points, 20, "PASS" if points >= 15 else "PARTIAL"))
        
    def check_query_functionality(self):
        """Test: Query & Answer Generation (50 points)"""
        self.print_section("TEST 4: Query & Answer Generation")
        total_points = 0
        
        for i, test in enumerate(TEST_QUESTIONS, 1):
            print(f"\n{'─'*70}")
            print(f"4.{i}. Question: \"{test['question']}\"")
            print(f"{'─'*70}")
            
            try:
                response = requests.post(
                    f"{API_BASE_URL}/query",
                    json={"question": test["question"], "k": 5},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    print(f"\nFull Response:")
                    print(f"   Status Code: {response.status_code}")
                    print(f"   Response Body:")
                    print(json.dumps(data, indent=4))
                    
                    if all(key in data for key in ["answer", "citations", "latencyMs"]):
                        points = 2
                        print(f"\n  ✓ Response structure correct")
                        
                        print(f"\nAnswer:")
                        print(f"   {data['answer']}")
                        
                        if data["answer"] and data["answer"] != "I could not find any relevant information to answer this question.":
                            points += 4
                            print(f"\n  ✓ Got a real answer (not default message)")
                            
                            if data["citations"] and len(data["citations"]) >= test["min_citations"]:
                                points += 4
                                print(f"  ✓ Has {len(data['citations'])} citation(s)")
                                
                                print(f"\nCitations:")
                                for j, citation in enumerate(data["citations"], 1):
                                    print(f"   [{j}] Doc ID: {citation.get('docId')}, Chunk ID: {citation.get('chunkId')}")
                            else:
                                print(f"  ✗ Missing or insufficient citations (expected {test['min_citations']}, got {len(data.get('citations', []))})")
                        else:
                            print(f"\n  ✗ No relevant answer found (got default/empty response)")
                    else:
                        points = 0
                        print(f"\n  ✗ Response missing required fields")
                        print(f"     Expected: answer, citations, latencyMs")
                        print(f"     Got: {list(data.keys())}")
                        
                    total_points += points
                    print(f"\n  Points: {points}/{test['points']}")
                else:
                    print(f"\n  ✗ Query failed with status: {response.status_code}")
                    print(f"     Response: {response.text}")
                    
            except Exception as e:
                print(f"\n  ✗ Error: {e}")
                import traceback
                traceback.print_exc()
                
        print(f"\n{'='*70}")
        self.total_points += total_points
        print(f"  Total Query Points: {total_points}/50")
        self.results.append(("Query Functionality", total_points, 50, "PASS" if total_points >= 35 else "PARTIAL"))
        
    def check_idempotency(self):
        """Test: Idempotency (10 points)"""
        self.print_section("TEST 5: Idempotency Check")
        points = 0
        
        # Ensure JAVA_HOME is set
        self.detect_java_home()
        
        try:
            conn = jaydebeapi.connect("org.h2.Driver", H2_JDBC_URL, ["sa", ""], H2_JAR_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DOC_ID, CHUNK_ID, COUNT(*) as cnt 
                FROM CHUNKS 
                GROUP BY DOC_ID, CHUNK_ID 
                HAVING COUNT(*) > 1
            """)
            duplicates = cursor.fetchall()
            
            if not duplicates:
                points = 10
                print(f"✓ No duplicate chunks found")
                
            else:
                print(f"✗ Found {len(duplicates)} duplicate chunk(s)")
                for doc_id, chunk_id, count in duplicates[:5]:  # Show first 5
                    print(f"   Doc {doc_id}, Chunk {chunk_id}: {count} copies")
                
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f" Could not check idempotency: {e}")
            points = 5
            
        self.total_points += points
        print(f"\n  Points: {points}/10")
        self.results.append(("Idempotency", points, 10, "PASS" if points == 10 else "FAIL"))
        
    def print_summary(self):
        """Print final grading summary"""
        self.print_section("GRADING SUMMARY")
        
        print(f"{'Test':<30} {'Score':<15} {'Status':<10}")
        print(f"{'-'*55}")
        for test_name, points, max_points, status in self.results:
            print(f"{test_name:<30} {points}/{max_points:<12} {status:<10}")
            
        print(f"{'-'*55}")
        print(f"{'TOTAL':<30} {self.total_points}/{self.max_points:<12}")
        print()
        
        percentage = (self.total_points / self.max_points) * 100
        if percentage >= 90:
            grade = "A"
        elif percentage >= 80:
            grade = "B"
        elif percentage >= 70:
            grade = "C"
        elif percentage >= 60:
            grade = "D"
        else:
            grade = "F"
            
        print(f"Final Score: {self.total_points}/{self.max_points} ({percentage:.1f}%)")
        print(f"Grade: {grade}")
        print()
        
    def save_results(self):
        """Save results to JSON file"""
        results_file = self.submission_dir / "grading_results.json"
        
        with open(results_file, "w") as f:
            json.dump({
                "submission_directory": str(self.submission_dir),
                "total_points": self.total_points,
                "max_points": self.max_points,
                "percentage": (self.total_points / self.max_points) * 100,
                "tests": [
                    {
                        "name": name,
                        "points": points,
                        "max_points": max_pts,
                        "status": status
                    }
                    for name, points, max_pts, status in self.results
                ]
            }, f, indent=2)
            
        print(f"Results saved to: {results_file}")
        
    def run(self):
        """Autograding workflow"""
        try:
            self.print_header()
            
            # Check submission structure
            if not self.check_submission_structure():
                return
                
            # Start API server
            if not self.start_api_server():
                print("\n✗ Cannot proceed without API server")
                return
                
            # Upload and process document
            if not self.upload_and_process_document():
                print("\n✗ Cannot proceed without processed document")
                return
                
            # Give it a moment to settle
            time.sleep(2)
            
            # Run tests
            self.check_api_health()
            self.check_upload_validation()
            self.check_database_chunks()
            self.check_query_functionality()
            self.check_idempotency()
            
            # Print summary
            self.print_summary()
            
            self.save_results()
            
        finally:
            self.cleanup()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        submission_dir = sys.argv[1]
    else:
        submission_dir = "."
        
    grader = FullAutograder(submission_dir)
    grader.run()