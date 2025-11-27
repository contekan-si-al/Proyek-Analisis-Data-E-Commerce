## Submission Dicoding : Belajar Analisis Data dengan Python

#### Proyek Analisis Data

*Repository* ini berisi proyek analisis data *e-commerce* yang aku kerjakan dan *deployment* ke **Streamlit**.

#### Deskripsi

Proyek ini akan menganalisis data [*Brazilian E-Commerce Public Dataset by Olist*](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).
Tujuannya adalah untuk menghasilkan *insight* yang berguna dari data yang dianalisis.

#### Struktur Direktori

- **/dashboard**: Direktori ini berisi `dashboard.py` yang digunakan untuk membuat *streamlit dashboard* hasil analisis data.
- **/data**: Direktori ini berisi *dataset* yang digunakan dalam proyek dengan *format* `.csv` .
- **Proyek Analisis Data.ipynb**: Berkas ini digunakan untuk melakukan analisis data.

#### Instalasi

1. *Clone repository* ke komputer lokal dengan menggunakan perintah berikut:

   ```bash
   git clone https://github.com/contekan-si-al/Proyek-Analisis-Data-E-Commerce.git   
   ```

2. Lakukan Instalasi Kaggle dan Konfigurasi Kaggle Api dengan cara sebagai berikut :
   
   [Kaggle Installation and API configuration](https://github.com/Kaggle/kaggle-api)
   
3. Pastikan kamu punya lingkungan Python yang sesuai dan pustaka-pustaka yang diperlukan. Kamu dapat menginstal pustaka-pustaka tersebut dengan menjalankan perintah berikut:

   ```bash
   cd Proyek-Analisis-Data-E-Commerce
   
   pip install -r requirements.txt
   ```

#### Menggunakan Streamlit

1. Masuk ke direktori proyek (Local):

   ```bash
   cd dashboard
   pip install streamlit
   streamlit run streamlit.py
   ```

   Bisa juga dengan mengunjungi halaman ini [Olist E-Commerce Dashboard](https://al-andat-ecommerce.streamlit.app/)
