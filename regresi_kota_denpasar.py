import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import statsmodels.api as sm

# =====================================================
# 1. KONFIGURASI DASHBOARD
# =====================================================
st.set_page_config(
    page_title="Denpasar Insight | Dashboard Analisis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Warna dan tampilan
st.markdown("""
<style>
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        letter-spacing: -0.5px;
    }
    div[data-testid="stMetric"] {
        background: var(--secondary-background-color);
        padding: 18px;
        border-radius: 12px;
        border: 1px solid rgba(128,128,128,0.18);
    }
    div[data-testid="stMetricLabel"] {
        font-size: 14px;
    }
    section[data-testid="stSidebar"] {
        border-right: 1px solid rgba(128,128,128,0.2);
    }
</style>
""", unsafe_allow_html=True)

# =====================================================
# 2. MEMBACA DATASET
# =====================================================
FILE = "dataset_fiskal_97_hipoFull (1).csv"

@st.cache_data
def load_data():
    df = pd.read_csv(FILE)
    df.columns = df.columns.str.strip()

    if "Kota" not in df.columns:
        raise ValueError(
            "Kolom 'Kota' tidak ditemukan. Periksa nama kolom CSV."
        )

    df["Kota"] = df["Kota"].astype("string").str.strip()

    if "Tahun" in df.columns:
        df["Tahun"] = pd.to_numeric(
            df["Tahun"], errors="coerce"
        )

    return df

try:
    data = load_data()
except Exception as e:
    st.error("Dataset gagal dibaca.")
    st.code(str(e))
    st.info(
        "Pastikan file CSV berada di folder yang sama "
        "dengan streamlit_app.py di GitHub."
    )
    st.stop()

if data.empty:
    st.error("Dataset tidak memiliki baris data.")
    st.stop()

# =====================================================
# 3. MENYIAPKAN DATA
# =====================================================
kota_list = sorted(data["Kota"].dropna().unique().tolist())

def cari_kota_denpasar(kota):
    return "denpasar" in str(kota).strip().lower()

denpasar_list = [k for k in kota_list if cari_kota_denpasar(k)]

if not denpasar_list:
    st.error(
        "Kota Denpasar tidak ditemukan dalam kolom Kota. "
        "Periksa ejaan nama kota pada dataset."
    )
    st.write("Kota yang tersedia:", kota_list)
    st.stop()

KOTA_UTAMA = denpasar_list[0]

numeric_cols = [
    col for col in data.select_dtypes(include="number").columns
    if col != "Tahun"
]

if not numeric_cols:
    st.error("Tidak ditemukan variabel numerik untuk dianalisis.")
    st.stop()

# =====================================================
# 4. SIDEBAR DAN FILTER
# =====================================================
st.sidebar.title("📊 Denpasar Insight")
st.sidebar.caption("City Data & Analytics")
st.sidebar.divider()

halaman = st.sidebar.radio(
    "NAVIGASI",
    [
        "🏠 Beranda",
        "🏙️ Perbandingan Kota",
        "🔎 Eksplorasi Data",
        "📈 Analisis Regresi",
        "📂 Data & Unduhan"
    ]
)

st.sidebar.divider()
st.sidebar.subheader("Filter Data")

if "Tahun" in data.columns and data["Tahun"].notna().any():
    tahun_tersedia = sorted(
        data["Tahun"].dropna().astype(int).unique().tolist()
    )

    tahun_pilihan = st.sidebar.slider(
        "Rentang tahun",
        min_value=min(tahun_tersedia),
        max_value=max(tahun_tersedia),
        value=(min(tahun_tersedia), max(tahun_tersedia))
    )

    data_filter = data[
        data["Tahun"].between(
            tahun_pilihan[0], tahun_pilihan[1]
        )
    ].copy()
else:
    data_filter = data.copy()

kota_pembanding = st.sidebar.multiselect(
    "Kota pembanding",
    options=[k for k in kota_list if k != KOTA_UTAMA],
    default=[k for k in kota_list if k != KOTA_UTAMA][:4]
)

data_denpasar = data_filter[
    data_filter["Kota"] == KOTA_UTAMA
].copy()

data_perbandingan = data_filter[
    data_filter["Kota"].isin(
        [KOTA_UTAMA] + kota_pembanding
    )
].copy()

# =====================================================
# 5. HEADER
# =====================================================
st.title("Denpasar Insight")
st.markdown(
    "Dashboard profesional untuk **perbandingan antar kota, "
    "eksplorasi data, dan analisis statistik**."
)

st.caption(
    f"Fokus utama: {KOTA_UTAMA}  |  "
    f"Total kota dalam dataset: {data['Kota'].nunique()}"
)

# =====================================================
# 6. BERANDA
# =====================================================
if halaman == "🏠 Beranda":

    st.subheader("Ringkasan Indikator Kota Denpasar")

    if data_denpasar.empty:
        st.warning("Tidak ada data Denpasar pada rentang tahun ini.")
        st.stop()

    k1, k2, k3, k4 = st.columns(4)

    k1.metric(
        "Jumlah Observasi",
        len(data_denpasar)
    )

    k2.metric(
        "Jumlah Variabel",
        len(numeric_cols)
    )

    if "IPM" in data_denpasar.columns:
        ipm = data_denpasar["IPM"].mean()
        k3.metric(
            "Rata-rata IPM",
            f"{ipm:.2f}" if pd.notna(ipm) else "N/A"
        )
    else:
        k3.metric("Rata-rata IPM", "Kolom tidak tersedia")

    if "PE" in data_denpasar.columns:
        pe = data_denpasar["PE"].mean()
        k4.metric(
            "Rata-rata PE",
            f"{pe:.2f}" if pd.notna(pe) else "N/A"
        )
    else:
        k4.metric("Rata-rata PE", "Kolom tidak tersedia")

    st.divider()

    kiri, kanan = st.columns(2)

    with kiri:
        st.subheader("Tren Indikator Denpasar")

        indikator_tren = st.selectbox(
            "Pilih indikator tren",
            numeric_cols,
            key="tren_denpasar"
        )

        if "Tahun" in data_denpasar.columns:
            tren = data_denpasar.dropna(
                subset=["Tahun", indikator_tren]
            ).sort_values("Tahun")

            fig = px.line(
                tren,
                x="Tahun",
                y=indikator_tren,
                markers=True,
                title=f"Tren {indikator_tren}",
                template="plotly_white"
            )

            fig.update_layout(
                margin=dict(l=10, r=10, t=55, b=10),
                hovermode="x unified"
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Kolom Tahun tidak tersedia.")

    with kanan:
        st.subheader("Profil Indikator Denpasar")

        nilai = data_denpasar[numeric_cols].mean().dropna()

        if not nilai.empty:
            profil = nilai.rename_axis(
                "Indikator"
            ).reset_index(name="Rata-rata")

            fig = px.bar(
                profil,
                x="Rata-rata",
                y="Indikator",
                orientation="h",
                title="Rata-rata Setiap Indikator",
                template="plotly_white"
            )

            fig.update_layout(
                yaxis={"categoryorder": "total ascending"},
                margin=dict(l=10, r=10, t=55, b=10)
            )

            st.plotly_chart(fig, use_container_width=True)

    st.subheader("Data Denpasar Terbaru")

    if "Tahun" in data_denpasar.columns:
        tampilan = data_denpasar.sort_values(
            "Tahun", ascending=False
        )
    else:
        tampilan = data_denpasar

    st.dataframe(
        tampilan.head(10),
        use_container_width=True,
        hide_index=True
    )

# =====================================================
# 7. PERBANDINGAN ANTAR KOTA
# =====================================================
elif halaman == "🏙️ Perbandingan Kota":

    st.subheader("Perbandingan Antar Kota")

    st.write(
        "Bandingkan indikator Denpasar dengan kota lain "
        "yang tersedia pada dataset."
    )

    indikator = st.selectbox(
        "Indikator yang dibandingkan",
        numeric_cols,
        key="indikator_perbandingan"
    )

    metode = st.radio(
        "Metode perbandingan",
        ["Rata-rata per kota", "Per tahun"],
        horizontal=True
    )

    if metode == "Rata-rata per kota":
        ringkasan = (
            data_perbandingan.groupby("Kota", as_index=False)[indikator]
            .mean()
            .dropna()
            .sort_values(indikator, ascending=False)
        )

        fig = px.bar(
            ringkasan,
            x="Kota",
            y=indikator,
            color="Kota",
            text_auto=".2f",
            title=f"Perbandingan Rata-rata {indikator}",
            template="plotly_white"
        )

    else:
        if "Tahun" not in data_perbandingan.columns:
            st.warning("Kolom Tahun tidak tersedia.")
            st.stop()

        ringkasan = data_perbandingan.dropna(
            subset=["Tahun", indikator]
        )

        fig = px.line(
            ringkasan,
            x="Tahun",
            y=indikator,
            color="Kota",
            markers=True,
            title=f"Tren {indikator} Antar Kota",
            template="plotly_white"
        )

    fig.update_layout(
        margin=dict(l=10, r=10, t=60, b=10),
        legend_title_text="Kota"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Tabel Perbandingan")
    st.dataframe(
        ringkasan,
        use_container_width=True,
        hide_index=True
    )

    if not ringkasan.empty:
        tertinggi = ringkasan.loc[
            ringkasan[indikator].idxmax()
        ]

        st.info(
            f"Nilai rata-rata tertinggi untuk {indikator} "
            f"pada data yang ditampilkan adalah "
            f"{tertinggi['Kota']} "
            f"({tertinggi[indikator]:.3f})."
        )

# =====================================================
# 8. EKSPLORASI DATA
# =====================================================
elif halaman == "🔎 Eksplorasi Data":

    st.subheader("Eksplorasi dan Hubungan Variabel")

    col1, col2 = st.columns(2)

    with col1:
        x_var = st.selectbox(
            "Variabel X",
            numeric_cols,
            index=numeric_cols.index("PAD")
            if "PAD" in numeric_cols else 0
        )

    with col2:
        y_var = st.selectbox(
            "Variabel Y",
            numeric_cols,
            index=numeric_cols.index("IPM")
            if "IPM" in numeric_cols else min(1, len(numeric_cols)-1)
        )

    kota_eksplorasi = st.multiselect(
        "Pilih kota untuk eksplorasi",
        kota_list,
        default=[KOTA_UTAMA]
    )

    eksplorasi = data_filter[
        data_filter["Kota"].isin(kota_eksplorasi)
    ].dropna(subset=[x_var, y_var]).copy()

    if x_var == y_var:
        st.warning("Pilih dua variabel yang berbeda.")
    elif eksplorasi.empty:
        st.warning("Tidak ada data lengkap untuk pilihan ini.")
    else:
        fig = px.scatter(
            eksplorasi,
            x=x_var,
            y=y_var,
            color="Kota",
            hover_data=["Tahun"] if "Tahun" in eksplorasi.columns else None,
            title=f"Hubungan {x_var} dengan {y_var}",
            template="plotly_white"
        )

        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Statistik Deskriptif")

    statistik = data_filter[numeric_cols].describe().T
    st.dataframe(statistik, use_container_width=True)

    st.subheader("Korelasi Antarvariabel")

    if len(numeric_cols) >= 2:
        korelasi = data_filter[numeric_cols].corr()

        fig = px.imshow(
            korelasi,
            text_auto=".2f",
            aspect="auto",
            color_continuous_scale="RdBu_r",
            zmin=-1,
            zmax=1,
            title="Matriks Korelasi",
            template="plotly_white"
        )

        st.plotly_chart(fig, use_container_width=True)

        st.caption(
            "Korelasi menunjukkan hubungan linear, "
            "bukan bukti sebab-akibat."
        )

# =====================================================
# 9. ANALISIS REGRESI
# =====================================================
elif halaman == "📈 Analisis Regresi":

    st.subheader("Regresi Linear")

    st.write(
        "Pilih variabel dependen (Y) dan satu atau lebih "
        "variabel independen (X). Model menggunakan observasi "
        "yang lengkap pada kota dan rentang tahun terpilih."
    )

    sumber_regresi = st.radio(
        "Cakupan data regresi",
        ["Kota Denpasar saja", "Semua kota terpilih"],
        horizontal=True
    )

    if sumber_regresi == "Kota Denpasar saja":
        regresi_data = data_denpasar.copy()
    else:
        regresi_data = data_perbandingan.copy()

    y_var = st.selectbox(
        "Variabel dependen (Y)",
        numeric_cols,
        index=numeric_cols.index("IPM")
        if "IPM" in numeric_cols else 0,
        key="reg_y"
    )

    pilihan_x = [c for c in numeric_cols if c != y_var]

    default_x = [
        c for c in ["PAD", "ICT"]
        if c in pilihan_x
    ]

    x_vars = st.multiselect(
        "Variabel independen (X)",
        pilihan_x,
        default=default_x,
        key="reg_x"
    )

    if st.button("Jalankan Analisis Regresi", type="primary"):

        if not x_vars:
            st.warning("Pilih setidaknya satu variabel X.")
        else:
            kolom_model = [y_var] + x_vars

            model_data = regresi_data[kolom_model].apply(
                pd.to_numeric, errors="coerce"
            ).replace([np.inf, -np.inf], np.nan).dropna()

            if len(model_data) <= len(x_vars) + 1:
                st.error(
                    "Observasi lengkap tidak cukup untuk "
                    "mengestimasi model ini."
                )
            else:
                X = sm.add_constant(
                    model_data[x_vars],
                    has_constant="add"
                )
                y = model_data[y_var]

                try:
                    model = sm.OLS(y, X).fit()

                    m1, m2, m3 = st.columns(3)

                    m1.metric(
                        "R-squared",
                        f"{model.rsquared:.4f}"
                    )
                    m2.metric(
                        "Adjusted R-squared",
                        f"{model.rsquared_adj:.4f}"
                    )
                    m3.metric(
                        "Observasi",
                        len(model_data)
                    )

                    st.subheader("Koefisien Regresi")

                    koefisien = pd.DataFrame({
                        "Koefisien": model.params,
                        "Std. Error": model.bse,
                        "t-statistik": model.tvalues,
                        "P-value": model.pvalues
                    })

                    st.dataframe(
                        koefisien,
                        use_container_width=True
                    )

                    st.subheader("Ringkasan Model")
                    st.code(model.summary().as_text())

                    st.subheader("Aktual dan Prediksi")

                    prediksi = model_data.copy()
                    prediksi["Prediksi"] = model.predict(X)

                    st.dataframe(
                        prediksi,
                        use_container_width=True
                    )

                    st.download_button(
                        "Unduh Hasil Regresi",
                        data=prediksi.to_csv(
                            index=False
                        ).encode("utf-8"),
                        file_name="hasil_regresi_denpasar.csv",
                        mime="text/csv"
                    )

                    st.caption(
                        "Interpretasi koefisien bergantung pada "
                        "satuan variabel dan spesifikasi model. "
                        "Periksa asumsi regresi dan kemungkinan "
                        "tren waktu sebelum menarik kesimpulan."
                    )

                except Exception as e:
                    st.error(f"Model gagal dihitung: {e}")

# =====================================================
# 10. DATA DAN UNDUHAN
# =====================================================
elif halaman == "📂 Data & Unduhan":

    st.subheader("Dataset Setelah Filter")

    st.write(
        f"Jumlah baris: {len(data_filter)} | "
        f"Jumlah kolom: {len(data_filter.columns)}"
    )

    cari = st.text_input(
        "Cari nama kota",
        placeholder="Contoh: Denpasar"
    )

    hasil = data_filter.copy()

    if cari:
        hasil = hasil[
            hasil["Kota"].str.contains(
                cari, case=False, na=False
            )
        ]

    st.dataframe(
        hasil,
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "📥 Unduh Dataset Hasil Filter",
        data=hasil.to_csv(index=False).encode("utf-8"),
        file_name="dataset_eksplorasi_kota.csv",
        mime="text/csv"
    )

    st.subheader("Informasi Data")
    info = pd.DataFrame({
        "Nama Kolom": data.columns,
        "Tipe Data": data.dtypes.astype(str).values,
        "Data Kosong": data.isna().sum().values
    })

    st.dataframe(info, use_container_width=True, hide_index=True)

# =====================================================
# 11. FOOTER
# =====================================================
st.divider()
st.caption(
    "Denpasar Insight | Dashboard eksplorasi dan analisis data. "
    "Interpretasi hasil perlu mempertimbangkan kualitas dan "
    "keterbatasan dataset."
)
