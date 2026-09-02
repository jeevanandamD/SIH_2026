import sqlite3

try:
    conn = sqlite3.connect('d:/Hackathon/SIH/SIH/sonaris.db')
    c = conn.cursor()
    # Survey Alpha: Shift west by 0.5 degrees
    c.execute("UPDATE sonar_images SET longitude = longitude - 0.5340 WHERE longitude > 72.8 AND longitude < 72.9 AND latitude > 18.9 AND latitude < 19.0")
    # Survey Charlie: Shift west by 0.4 degrees
    c.execute("UPDATE sonar_images SET longitude = longitude - 0.4000 WHERE longitude > 76.2 AND longitude < 76.3 AND latitude > 9.9 AND latitude < 10.0")
    # Survey Bravo: Shift to 9.7876, 79.5129
    c.execute("UPDATE sonar_images SET latitude = latitude + 0.5000, longitude = longitude + 0.2000 WHERE longitude > 79.3 AND longitude < 79.4 AND latitude > 9.2 AND latitude < 9.3")
    conn.commit()
    print('DB updated successfully')
except Exception as e:
    print('Error:', e)
finally:
    if 'conn' in locals():
        conn.close()
