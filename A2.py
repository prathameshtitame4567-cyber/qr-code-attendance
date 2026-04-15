import cv2
from pyzbar.pyzbar import decode
import time
import mysql.connector
from mysql.connector import Error
import datetime
import csv
import pywhatkit
import pyttsx3


try:
    engine = pyttsx3.init()
    voices = engine.getProperty("voices")
    if len(voices) > 1:
        engine.setProperty("voice", voices[1].id)
    else:
        engine.setProperty("voice", voices[0].id)
except Exception as e:
    print(f"Warning: Text-to-speech initialization failed: {e}")
    engine = None

def speak(text):
    """Helper function to handle text-to-speech safely"""
    if engine:
        try:
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"TTS Error: {e}")
    print(text)  # Always print the message

def countVal(dict_obj, value):
    """Count occurrences of a value in a dictionary"""
    count = 0
    for key, val in dict_obj.items():
        if val == value:
            count += 1
    return count

def connect_database():
    """Connect to MySQL database with error handling"""
    try:
        mydb = mysql.connector.connect(
            host="localhost",  
            user="root",       
            password="niku1234",  
            database="attendance_db"   
        )
        print("✓ Database connected successfully!")
        return mydb
    except Error as e:
        print(f"✗ Database connection failed: {e}")
        print("Continuing without database storage...")
        return None

def setup_database(mydb):
    """Create attendance table if it doesn't exist"""
    if mydb:
        try:
            mycursor = mydb.cursor()
            mycursor.execute("""
                CREATE TABLE IF NOT EXISTS Attendance (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255),
                    attendance VARCHAR(50),
                    date DATE,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            mydb.commit()
            print("✓ Database table ready!")
            return mycursor
        except Error as e:
            print(f"✗ Table creation failed: {e}")
            return None
    return None

def main():    
    mydb = connect_database()
    mycursor = setup_database(mydb)

    attendance_list = {
        'STUDENT NAME': 'Absent',      
        'Aarya Titame': 'Absent',          
        'Prathamesh Titame': 'Absent',        
                        'Shravani Khedkar': 'Absent',      
        'Tanmay Naik': 'Absent',   
    }
    
   
    
    scanned_names = set()  
    
    
    print("\n✓ Opening webcam...")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("✗ Error: Could not open webcam!")
        return
    
    print("✓ Webcam opened successfully!")
    print("\n📸 Scanning QR codes... Press 'q' to finish attendance\n")
    
    delay_time = 2  
    last_scan_time = {}

    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("✗ Error reading frame from webcam")
            break
        
        
        qr_codes = decode(frame)
        
        for qr_code in qr_codes:
            name = qr_code.data.decode('utf-8')
            current_time = time.time()
            
            
            if name in attendance_list:
                
                if name not in scanned_names:
                    attendance_list[name] = 'Present'
                    scanned_names.add(name)
                    
                    
                    print(f"\n{'='*50}")
                    print(f"✓ ATTENDANCE MARKED")
                    print(f"   Student: {name}")
                    print(f"   Status: PRESENT")
                    print(f"   Time: {datetime.datetime.now().strftime('%H:%M:%S')}")
                    print(f"{'='*50}\n")
                    
                    
                    speak(f"Attendance marked for {name}")
                    
                    
                    if mycursor and mydb:
                        try:
                            sql = "INSERT INTO Attendance (name, attendance, date) VALUES (%s, %s, %s)"
                            val = (name, 'Present', datetime.date.today())
                            mycursor.execute(sql, val)
                            mydb.commit()
                            print(f"✓ Database updated for {name}\n")
                        except Error as e:
                            print(f"✗ Database insert error: {e}\n")
                    
                    last_scan_time[name] = current_time
                    
                    
                    time.sleep(1)
                    
                else:
                    
                    if name not in last_scan_time or (current_time - last_scan_time[name] > 3):
                        print(f"ℹ {name} - Already marked present")
                        last_scan_time[name] = current_time
            else:
                
                if name not in last_scan_time or (current_time - last_scan_time[name] > 3):
                    print(f"⚠ WARNING: Unknown student QR code detected: {name}")
                    last_scan_time[name] = current_time
            
            
            points = qr_code.polygon
            if len(points) == 4:
                pts = [(point.x, point.y) for point in points]
                
                if name in scanned_names:
                    color = (0, 255, 0)  # Green - Present
                    status_text = "PRESENT"
                elif name in attendance_list:
                    color = (0, 255, 255)  # Yellow - Ready to scan
                    status_text = "READY"
                else:
                    color = (0, 0, 255)  # Red - Unknown
                    status_text = "UNKNOWN"
                
                for i in range(4):
                    cv2.line(frame, pts[i], pts[(i+1)%4], color, 3)
                
                
                cv2.putText(frame, f"{name} - {status_text}", 
                           (qr_code.rect.left, qr_code.rect.top - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        
        overlay_height = 80
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (frame.shape[1], overlay_height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        
        present = len(scanned_names)
        total = len(attendance_list)
        cv2.putText(frame, f"Present: {present}/{total}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "Press 'Q' to finish", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        
        cv2.imshow('QR Code Attendance System', frame)
        
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    
    cap.release()
    cv2.destroyAllWindows()
    
    
    present_count = countVal(attendance_list, "Present")
    absent_count = countVal(attendance_list, "Absent")
    
    print("\n" + "="*50)
    print("ATTENDANCE SUMMARY")
    print("="*50)
    print(f"Total Present: {present_count}")
    print(f"Total Absent: {absent_count}")
    print("\nDetailed Attendance:")
    for name, status in attendance_list.items():
        print(f"  {name}: {status}")
    print("="*50 + "\n")
    
    
    try:
        with open('attendance.csv', mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Name', 'Attendance', 'Date'])
            for name, attendance in attendance_list.items():
                writer.writerow([name, attendance, datetime.date.today()])
        print("✓ Attendance saved to attendance.csv")
    except Exception as e:
        print(f"✗ CSV save error: {e}")
    
    # Get subject and day information
    speak("The attendance has been taken. For which subject?")
    subject = input("Enter subject (cse/eee/chem/mat/mec): ").lower().strip()
    
    speak("On which day?")
    day = input("Enter day: ").lower().strip()
    
    
    present_list = [name for name, attendance in attendance_list.items() if attendance == 'Present']
    absent_list = [name for name, attendance in attendance_list.items() if attendance == 'Absent']
    
    message = f"""📋 Attendance Report
Subject: {subject.upper()}
Day: {day.capitalize()}
Date: {datetime.date.today()}

✓ Present ({present_count}): {', '.join(present_list) if present_list else 'None'}
✗ Absent ({absent_count}): {', '.join(absent_list) if absent_list else 'None'}"""
    
    print("\n" + message)
    
    
    send_whatsapp = input("\nDo you want to send WhatsApp message? (yes/no): ").lower().strip()
    
    if send_whatsapp == 'yes':
        phone_number = input("Enter faculty WhatsApp number (with country code, e.g., +919876543210): ")
        
        
        now = datetime.datetime.now()
        send_time = now + datetime.timedelta(minutes=2)
        
        speak("Attendance has been taken and will be sent to the concerned faculty")
        
        try:
            print(f"\nScheduling WhatsApp message for {send_time.strftime('%H:%M')}...")
            pywhatkit.sendwhatmsg(phone_number, message, send_time.hour, send_time.minute)
            print("✓ WhatsApp message scheduled!")
        except Exception as e:
            print(f"✗ WhatsApp send error: {e}")
            print("Make sure WhatsApp Web is logged in on your default browser")
    
    speak("Thank you! See you in the next class")
    
    
    if mydb:
        mydb.close()
        print("\n✓ Database connection closed")

if __name__ == "__main__":
    cap = None  # Initialize camera variable
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ Program interrupted by user")
        # Force release camera
        try:
            cv2.destroyAllWindows()
            if 'cap' in globals() and cap is not None:
                cap.release()
        except:
            pass
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        # Force release camera
        try:
            cv2.destroyAllWindows()
            if 'cap' in globals() and cap is not None:
                cap.release()
        except:
            pass
    finally:
        
        print("\n🔄 Cleaning up camera resources...")
        cv2.destroyAllWindows()
        time.sleep(0.5)  
        print("✓ Cleanup complete")