import qrcode
import os

def generate_qr_code(name, folder_path):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(name)
    qr.make(fit=True)

    os.makedirs(folder_path, exist_ok=True)

    qr.make_image(fill_color="black", back_color="white").save(
        os.path.join(folder_path, "qr_code.png")
    )

    print("QR code generated successfully and saved in the specified folder!")

# Data to encode
name = "Siddhanth Walke"

# Folder path
folder_path = r"C:\Users\Siddhanth\OneDrive\SEM 5\QR_CODE-ATTENDANCE-SYSTEM---Scan-Attend--main"

# Generate QR
generate_qr_code(name, folder_path)
