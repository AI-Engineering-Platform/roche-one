import json
import argparse
import logging
from pathlib import Path


def setup_logging(log_level: str):
    """
    Set up logging configuration with the specified log level.
    
    Args:
        log_level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def parse_and_split_studies():
    """
    Read JSON files from data/studies/combined-studies/ folder,
    extract individual studies, and save them to data/studies/split-studies/
    """
    # Get the project root directory (parent of src)
    project_root = Path(__file__).parent.parent.parent
    combined_studies_dir = project_root / "data" / "studies" / "combined-studies"
    split_studies_dir = project_root / "data" / "studies" / "split-studies"
    
    # Create split-studies directory if it doesn't exist
    split_studies_dir.mkdir(parents=True, exist_ok=True)
    
    # Get all JSON files from combined-studies directory
    json_files = list(combined_studies_dir.glob("*.json"))
    
    if not json_files:
        logging.warning(f"No JSON files found in {combined_studies_dir}")
        return
    
    logging.info(f"Found {len(json_files)} JSON file(s) to process")
    
    total_studies = 0
    
    # Process each JSON file
    for json_file in json_files:
        logging.info(f"Processing {json_file.name}...")
        
        try:
            # Read the JSON file
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract studies list
            if "studies" not in data:
                logging.warning(f"No 'studies' property found in {json_file.name}")
                continue
            
            studies = data["studies"]
            logging.info(f"Found {len(studies)} study(ies)")
            
            # Process each study
            for study in studies:
                try:
                    # Extract nctId from the study
                    nct_id = study.get("protocolSection", {}).get("identificationModule", {}).get("nctId")
                    
                    if not nct_id:
                        logging.warning(f"Study missing nctId, skipping...")
                        continue
                    
                    # Create output filename using nctId
                    output_file = split_studies_dir / f"{nct_id}.json"
                    
                    # Save the study to a separate JSON file
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(study, f, indent=2, ensure_ascii=False)
                    
                    total_studies += 1
                    logging.info(f"Saved study: {nct_id}.json")
                    
                except Exception as e:
                    logging.error(f"Error processing study: {e}")
                    continue
        
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in {json_file.name}: {e}")
            continue
        except Exception as e:
            logging.error(f"Error reading {json_file.name}: {e}")
            continue
    
    logging.info(f"Complete! Processed {total_studies} study(ies) total")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Parse and split study JSON files')
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Set the logging level (default: INFO)'
    )
    
    args = parser.parse_args()
    setup_logging(args.log_level)
    parse_and_split_studies()

