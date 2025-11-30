from musicai_sdk import MusicAiClient
import os

def process_audio_with_music_ai(api_key, workflow_name, mp3_file_path, output_dir, verbose=True):
    """
    Process audio file with Music.AI SDK and download results.
    
    Args:
        api_key (str): Music.AI API key
        workflow_name (str): Workflow name to use
        mp3_file_path (str): Path to the MP3 file
        output_dir (str): Directory to save results
        verbose (bool): Print progress messages
    
    Returns:
        dict: Contains 'success' (bool), 'lyrics_file' (str), 'chords_files' (list), 'stem_files' (list), 'job_id' (str)
    """
    try:
        if verbose:
            print("=" * 60)
            print("Music.AI Processing Pipeline (Using SDK)")
            print("=" * 60)
        
        # Initialize the client
        if verbose:
            print("\nStep 1: Initializing Music.AI client...")
        music_ai = MusicAiClient(api_key=api_key)
        if verbose:
            print("✓ Client initialized")
        
        # Step 2: Upload file
        if verbose:
            print(f"\nStep 2: Uploading file ({mp3_file_path})...")
        if not os.path.exists(mp3_file_path):
            raise FileNotFoundError(f"File not found: {mp3_file_path}")
        
        song_url = music_ai.upload_file(mp3_file_path)
        if verbose:
            print(f"✓ File uploaded successfully")
            print(f"  Download URL: {song_url}")

        # Step 3: Create job
        if verbose:
            print(f"\nStep 3: Creating job...")
        job_result = music_ai.add_job(
            "Computação Musical",
            workflow_name,
            {"inputAudio": song_url},
        )
        job_id = job_result["id"]
        if verbose:
            print(f"✓ Job created with ID: {job_id}")
        
        # Step 4: Wait for job completion
        if verbose:
            print(f"\nStep 4: Waiting for job completion...")
        job = music_ai.wait_for_job_completion(job_id)
        
        # Step 5: Check job status and download results
        if verbose:
            print(f"\nStep 5: Processing results...")
        
        if job["status"] == "SUCCEEDED":
            if verbose:
                print(f"✓ Job completed successfully!")
                print(f"  Job Info:")
                print(f"    Name: {job.get('name')}")
                print(f"    Workflow: {job.get('workflow')}")
                print(f"    Status: {job.get('status')}")
                print(f"    Created: {job.get('createdAt')}")
                print(f"    Completed: {job.get('completedAt')}")
            
            # Step 6: Download results
            if verbose:
                print(f"\nStep 6: Downloading results...")
            os.makedirs(output_dir, exist_ok=True)
            result_files = music_ai.download_job_results(job, output_dir)
            
            # Find lyrics and chords files
            lyrics_file = None
            chords_files = []
            stem_files = []
            
            for file_path in result_files:
                if "lyrics" in file_path.lower() or "chords" in file_path.lower():
                    file_path = file_path + ".json"
                elif "stem" in file_path.lower():
                    file_path = file_path + ".wav"
                
                file_path = os.path.join(output_dir, file_path)
                
                if os.path.exists(file_path):
                    if "lyrics" in file_path.lower():
                        lyrics_file = file_path
                    elif "chords" in file_path.lower():
                        chords_files.append(file_path)
                    elif "stem" in file_path.lower():
                        stem_files.append(file_path)
                    else:
                        print(f"File is not classified: {file_path}")
                else:
                    print(f"File does not exist: {file_path}")
            
            if verbose:
                print(f"✓ Results downloaded successfully:")
                for file_path in result_files:
                    print(f"  - {file_path}")
            
            if verbose:
                print("\n" + "=" * 60)
                print("✓ Pipeline completed successfully!")
                print("=" * 60)
            
            return {
                "success": True,
                "lyrics_file": lyrics_file,
                "chords_files": chords_files,
                "stem_files": stem_files,
                "job_id": job_id,
                "message": "Processing completed successfully"
            }
        else:   
            if verbose:
                print(f"✗ Job failed with status: {job['status']}")
                if job.get("error"):
                    error = job["error"]
                    print(f"  Error Code: {error.get('code')}")
                    print(f"  Error Title: {error.get('title')}")
                    print(f"  Error Message: {error.get('message')}")
            
            # Clean up failed job
            if verbose:
                print(f"\nCleaning up job {job_id}...")
            # music_ai.delete_job(job_id)
            
            return {
                "success": False,
                "job_id": job_id,
                "message": f"Job failed with status: {job['status']}"
            }
        
    except Exception as e:
        if verbose:
            print(f"\n✗ Error: {e}")
        return {
            "success": False,
            "message": str(e)
        }