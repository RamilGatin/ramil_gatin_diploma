import os
import subprocess

# URL для загрузки данных
url = "https://nrt3.modaps.eosdis.nasa.gov/api/v2/content/archives/FIRMS/modis-c6.1/Russia_Asia"

# Укажите ваш токен авторизации здесь
token = "eyJ0eXAiOiJKV1QiLCJvcmlnaW4iOiJFYXJ0aGRhdGEgTG9naW4iLCJzaWciOiJlZGxqd3RwdWJrZXlfb3BzIiwiYWxnIjoiUlMyNTYifQ.eyJ0eXBlIjoiVXNlciIsInVpZCI6InNmbnVya2FldiIsImV4cCI6MTcxOTc1MzA2MiwiaWF0IjoxNzE0NTY5MDYyLCJpc3MiOiJFYXJ0aGRhdGEgTG9naW4ifQ.0yfl8CZVuAdqYda_l3JcjwU-rXCvtHchiNy3-r3e9PQQHEClCa94x0ir_cb1cMUs_20ktGPGyEhhFu1lgAA28_mWuUEAVRLotQKxGAfzH-xoN2jFNh5A9R6eWaUL4JDLqwOd-zQXmfylQJXv4PR9lF0xZDwhdtfpogpT_FRfkCwuOGBgzTUP5aSRL5yJKhPDEW0fy9iYXk5F_caus-PuoMincM16_2el-KHrx6muh-ibOJl_WcmgY6_z0Dhb6E4kgkNKeQ8mQKE7zApnCMhcXgQDPu-dh2gu131lpfkTkGNcFxCIRg6dAz-9qqDDgEScryN08N3wzLE0W2Z6winLJQ"

# Директория для сохранения данных
data_dir = "data/FIRMS/modis-c6.1/Russia_Asia"
os.makedirs(data_dir, exist_ok=True)


def download_data():
    command = [
        "wget",
        "-q",
        "-e",
        "robots=off",
        "-m",
        "-np",
        "-R",
        ".html,.tmp",
        "-nH",
        "--cut-dirs=4",
        url,
        "--header",
        f"Authorization: Bearer {token}",
        "-P",
        data_dir,
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode == 0:
        print("Data downloaded successfully.")
    else:
        print(f"Failed to download data. Error: {result.stderr}")


if __name__ == "__main__":
    download_data()
