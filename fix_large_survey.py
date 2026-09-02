import sqlite3

try:
    conn = sqlite3.connect('d:/Hackathon/SIH/SIH/sonaris.db')
    c = conn.cursor()
    
    # We only want to shift the points that were generated from the ZIP upload bug.
    # Those points started at 15.4208, 73.7845 and went diagonally North-East.
    # We will shift them West by 1.5 degrees and South by 0.5 degrees to put them firmly in the Arabian Sea.
    query = """
    UPDATE sonar_images 
    SET 
        longitude = longitude - 1.5,
        latitude = latitude - 0.5
    WHERE 
        latitude >= 15.0 AND latitude <= 18.0
        AND longitude >= 73.5 AND longitude <= 76.0
    """
    
    c.execute(query)
    conn.commit()
    print('Points successfully moved into the ocean.')
except Exception as e:
    print('Error:', e)
finally:
    if 'conn' in locals():
        conn.close()
