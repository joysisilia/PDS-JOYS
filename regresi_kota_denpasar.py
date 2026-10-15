import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="CityInsight | Analisis Kota",
    page_icon="🏙️",
    layout="wide"
)

# =========================
# DATA CONTOH
# =========================
data = pd.DataFrame({
    "Kota": ["Jakarta", "Bandung", "Surabaya", "Medan", "Makassar"],
    "IPM": [83.5, 82.3, 82.1, 75.2, 82.4],
    "Pertumbuhan Ekonomi (%)": [4.9, 5.4, 5.1, 4.8, 5.0],
    "Pengangguran (%)": [6.2, 7.2, 5.5, 7.0, 5.8],
    "Pendapatan per Kapita (Juta Rp)": [120.5, 78.3, 74.6, 52.7, 68.9]
})

# =========================
# SIDEBAR
# =========================
st.sidebar.title("🏙️ CityInsight")
st.sidebar.caption("Perbandingan & Eksplorasi Data Kota")

halaman = st.sidebar.radio(
    "Navigasi",
    ["Beranda", "Perbandingan Kota",
     "Eksplorasi Data", "Analisis Mendalam"]
)

st.sidebar.divider()
st.sidebar.caption("Dashboard analisis data perkotaan")

# =========================
# FILTER DATA
# =========================
st.title("Dashboard Analisis Antar Kota")
st.write(
    "Bandingkan indikator pembangunan dan ekonomi "
    "serta eksplorasi hubungan antarvariabel."
)

pilihan_kota = st.multiselect(
    "Pilih kota untuk dianalisis",
    data["Kota"].tolist(),
    default=data["Kota"].tolist()
)

df = data[data["Kota"].isin(pilihan_kota)]

if df.empty:
    st.warning("Pilih minimal satu kota untuk menampilkan analisis.")
    st.stop()

# =========================
# BERANDA
# =========================
if halaman == "Beranda":
    st.subheader("Ringkasan Data")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Jumlah Kota", len(df))
    c2.metric("Rata-rata IPM", f"{df['IPM'].mean():.2f}")
    c3.metric(
        "Rata-rata Pertumbuhan",
        f"{df['Pertumbuhan Ekonomi (%)'].mean():.2f}%"
    )
    c4.metric(
        "Rata-rata Pengangguran",
        f"{df['Pengangguran (%)'].mean():.2f}%"
    )

    st.divider()

    kiri, kanan = st.columns(2)

    with kiri:
        st.subheader("Perbandingan IPM")
        fig = px.bar(
            df.sort_values("IPM", ascending=False),
            x="Kota",
            y="IPM",
            color="Kota",
            text="IPM",
            title="Indeks Pembangunan Manusia"
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with kanan:
        st.subheader("Pertumbuhan Ekonomi")
        fig = px.bar(
            df,
            x="Kota",
            y="Pertumbuhan Ekonomi (%)",
            color="Kota",
            title="Pertumbuhan Ekonomi per Kota"
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Data Perbandingan Kota")
    st.dataframe(df, use_container_width=True, hide_index=True)

    if len(df) > 0:
        kota_ipm = df.loc[df["IPM"].idxmax()]
        st.info(
            f"IPM tertinggi pada data contoh ini adalah "
            f"{kota_ipm['Kota']} "
            f"({kota_ipm['IPM']:.1f})."
        )

# =========================
# PERBANDINGAN KOTA
# =========================
elif halaman == "Perbandingan Kota":
    st.subheader("Perbandingan Indikator")

    indikator = st.selectbox(
        "Pilih indikator",
        [
            "IPM",
            "Pertumbuhan Ekonomi (%)",
            "Pengangguran (%)",
            "Pendapatan per Kapita (Juta Rp)"
        ]
    )

    fig = px.bar(
        df.sort_values(indikator, ascending=False),
        x="Kota",
        y=indikator,
        color="Kota",
        text=indikator,
        title=f"Perbandingan {indikator} Antar Kota"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Peringkat Kota")
    peringkat = df.sort_values(indikator, ascending=False)
    st.dataframe(peringkat, use_container_width=True, hide_index=True)

# =========================
# EKSPLORASI DATA
# =========================
elif halaman == "Eksplorasi Data":
    st.subheader("Eksplorasi Variabel")

    x_var = st.selectbox(
        "Variabel sumbu X",
        data.select_dtypes(include="number").columns,
        index=3
    )

    y_var = st.selectbox(
        "Variabel sumbu Y",
        data.select_dtypes(include="number").columns,
        index=0
    )

    fig = px.scatter(
        df,
        x=x_var,
        y=y_var,
        color="Kota",
        text="Kota",
        hover_data=["IPM", "Pertumbuhan Ekonomi (%)"],
        title=f"Hubungan {x_var} dan {y_var}"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Statistik Deskriptif")
    st.dataframe(
        df.select_dtypes(include="number").describe().T,
        use_container_width=True
    )

    st.download_button(
        "📥 Unduh Data CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="data_perbandingan_kota.csv",
        mime="text/csv"
    )

# =========================
# ANALISIS MENDALAM
# =========================
elif halaman == "Analisis Mendalam":
    st.subheader("Analisis Korelasi")

    angka = df.select_dtypes(include="number")

    if len(angka.columns) >= 2 and len(df) >= 2:
        korelasi = angka.corr()

        fig = px.imshow(
            korelasi,
            text_auto=".2f",
            color_continuous_scale="RdBu_r",
            zmin=-1,
            zmax=1,
            title="Matriks Korelasi Antarindikator"
        )
        st.plotly_chart(fig, use_container_width=True)

        st.write(
            "Korelasi menunjukkan arah dan kekuatan hubungan "
            "linear antarvariabel. Korelasi tidak membuktikan "
            "hubungan sebab-akibat."
        )
    else:
        st.warning(
            "Pilih minimal dua kota agar korelasi dapat dihitung."
        )

    st.subheader("Ringkasan Statistik")
    st.write(angka.describe())
