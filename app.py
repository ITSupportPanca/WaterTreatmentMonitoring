import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import uuid
import io
from github import Github

# =========================================================
# 1. CONFIG UTAMA WEBSITE
# =========================================================
st.set_page_config(page_title="WTP Multi-System Monitoring", layout="wide", page_icon="💧")

# Ambil kredensial dari Streamlit Secrets
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    GITHUB_REPO = st.secrets["GITHUB_REPO"]
    FILE_PATH = "database_wtp.xlsx"
except Exception:
    st.error("❌ Token atau Nama Repo GitHub belum di-setting di Streamlit Secrets, bro!")
    st.stop()

MASTER_COLUMNS = [
    "ID_Data", "Teknisi", "Plant", "Modul", "Unit_Titik", "Tanggal",
    "pH", "Conduct", "TDS", "Tot_Hardness", "M_Alkalinity", "Silica",
    "Chloride", "Iron", "Turbidity", "O_Phosphate", "LSI", "Sulfit",
]

UNIT_OPTIONS = {
    "BOILER": ["Deaerator", "WHB Off Gass 1", "WHB Off Gass 2", "WHB Plant 1", "WHB Plant 2"],
    "COOLING TOWER": ["SBR", "Reject RO", "Batch Plant 1 (BP 1)", "Batch Plant 2 (BP 2)"],
    "CHILLER": ["RO Chiller", "Chiller Tank"],
}


# =========================================================
# 2. FUNGSI DATA: BACA & SIMPAN KE GITHUB
# =========================================================
@st.cache_data(ttl=5)
def load_data_from_github():
    """Ambil database master dari file Excel di GitHub."""
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)
        file_content = repo.get_contents(FILE_PATH)
        data_bytes = file_content.decoded_content
        df = pd.read_excel(io.BytesIO(data_bytes))
        return df, file_content.sha
    except Exception:
        # File belum ada di GitHub -> inisialisasi struktur kosong
        df_init = pd.DataFrame(columns=MASTER_COLUMNS)
        return df_init, None


def save_data_to_github(df: pd.DataFrame) -> bool:
    """Push dataframe terbaru kembali ke file Excel di GitHub."""
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        excel_data = output.getvalue()

        _, sha = load_data_from_github()
        if sha:
            repo.update_file(FILE_PATH, "Update database WTP Treatment via Web App", excel_data, sha)
        else:
            repo.create_file(FILE_PATH, "Inisialisasi database master WTP via Web App", excel_data)
        return True
    except Exception as e:
        st.error(f"Gagal push ke GitHub: {e}")
        return False


# =========================================================
# 3. RENDER HELPERS (dipakai di beberapa tab)
# =========================================================
def render_trend_charts(df_filtered: pd.DataFrame, modul: str):
    """Render 6 grafik tren inti + grafik tambahan spesifik modul."""
    c_g1, c_g2 = st.columns(2)
    with c_g1:
        fig_ph = px.line(df_filtered, x="Tanggal", y="pH", color="Unit_Titik",
                          title="1. Tren Perbandingan pH Air", markers=True)
        st.plotly_chart(fig_ph, use_container_width=True)
    with c_g2:
        fig_cond = px.line(df_filtered, x="Tanggal", y="Conduct", color="Unit_Titik",
                            title="2. Tren Conductivity (uS/cm)", markers=True)
        st.plotly_chart(fig_cond, use_container_width=True)

    c_g3, c_g4 = st.columns(2)
    with c_g3:
        fig_hard = px.line(df_filtered, x="Tanggal", y="Tot_Hardness", color="Unit_Titik",
                            title="3. Tren Kalsium / Total Hardness (ppm)", markers=True)
        st.plotly_chart(fig_hard, use_container_width=True)
    with c_g4:
        fig_malk = px.line(df_filtered, x="Tanggal", y="M_Alkalinity", color="Unit_Titik",
                            title="4. Tren Kadar M-Alkalinity", markers=True)
        st.plotly_chart(fig_malk, use_container_width=True)

    c_g5, c_g6 = st.columns(2)
    with c_g5:
        fig_sil = px.line(df_filtered, x="Tanggal", y="Silica", color="Unit_Titik",
                           title="5. Tren Kandungan Silica Pengendap (ppm)", markers=True)
        st.plotly_chart(fig_sil, use_container_width=True)
    with c_g6:
        fig_chlor = px.line(df_filtered, x="Tanggal", y="Chloride", color="Unit_Titik",
                             title="6. Tren Korosivitas Chloride", markers=True)
        st.plotly_chart(fig_chlor, use_container_width=True)

    # Grafik tambahan spesifik modul
    st.markdown("---")
    if modul == "COOLING TOWER":
        fig_lsi = px.bar(df_filtered, x="Tanggal", y="LSI", color="Unit_Titik",
                          title="7. Grafik Indeks Kejenuhan Langelier (LSI Index)", barmode="group")
        st.plotly_chart(fig_lsi, use_container_width=True)
    elif modul == "BOILER":
        fig_sulf = px.line(df_filtered, x="Tanggal", y="Sulfit", color="Unit_Titik",
                            title="7. Tren Kadar Sulfit Pengikat Oksigen (ppm)", markers=True)
        st.plotly_chart(fig_sulf, use_container_width=True)


# =========================================================
# 4. LOAD DATA & ROUTING HALAMAN (SHARE LINK vs MAIN APP)
# =========================================================
df_data, _ = load_data_from_github()
query_params = st.query_params

if "id" in query_params:
    # -----------------------------------------------------
    # HALAMAN: LINK SHARE (VIEW ONLY)
    # -----------------------------------------------------
    share_id = query_params["id"]
    df_shared = df_data[df_data["ID_Data"] == share_id]

    if df_shared.empty:
        st.error("❌ Link tidak valid atau data tidak ditemukan.")
    else:
        st.title("💧 Shared Dashboard - WTP Treatment Program")
        info_row = df_shared.iloc[0]
        st.info(
            f"👀 Mode: Lihat Saja. Teknisi: {info_row['Teknisi']} | "
            f"Lokasi: {info_row['Plant']} | Modul: {info_row['Modul']}"
        )

        df_module_plant = df_data[
            (df_data["Modul"] == info_row["Modul"]) & (df_data["Plant"] == info_row["Plant"])
        ]

        c1, c2 = st.columns(2)
        with c1:
            fig_ph = px.line(df_module_plant, x="Tanggal", y="pH", color="Unit_Titik",
                              title="Tren pH Air", markers=True)
            st.plotly_chart(fig_ph, use_container_width=True)
        with c2:
            fig_cond = px.line(df_module_plant, x="Tanggal", y="Conduct", color="Unit_Titik",
                                title="Tren Conductivity", markers=True)
            st.plotly_chart(fig_cond, use_container_width=True)

        st.markdown("### 📋 Tabel Data Pemantauan")
        st.dataframe(df_shared.drop(columns=["ID_Data"], errors="ignore"), use_container_width=True)

        if st.button("⬅️ Buka Aplikasi Utama"):
            st.query_params.clear()
            st.rerun()

else:
    # -----------------------------------------------------
    # HALAMAN: UTAMA (INPUT, LIVE DASHBOARD, EDIT)
    # -----------------------------------------------------
    st.title("🏭 WTP Treatment Quality Control & Monitoring Master System")

    # --- Sidebar: autentikasi & lokasi ---
    st.sidebar.markdown("### 🧑‍💻 Autentikasi & Lokasi")
    nama_teknisi = st.sidebar.text_input("Nama Teknisi / Surveyor (Wajib)", placeholder="Ketik nama Anda...")
    pilihan_plant = st.sidebar.selectbox("Pilih Wilayah Kerja (Plant):", ["Plant A", "Plant B"])
    pilihan_modul = st.sidebar.selectbox("Pilih Modul Monitoring:", ["BOILER", "COOLING TOWER", "CHILLER"])

    tab_form, tab_dash, tab_kelola = st.tabs(
        ["📝 Form Input Lab Harian", "📊 Dashboard Analisis & Share", "⚙️ Kelola / Edit Data"]
    )

    # =====================================================
    # TAB 1: FORM INPUT UTAMA
    # =====================================================
    with tab_form:
        st.subheader(f"Form Input Data Lab - {pilihan_modul} ({pilihan_plant})")

        list_unit = UNIT_OPTIONS[pilihan_modul]

        with st.form("master_wtp_form", clear_on_submit=True):
            col_h1, col_h2 = st.columns(2)
            with col_h1:
                tgl = st.date_input("Tanggal Sampling", datetime.date.today())
            with col_h2:
                val_unit = st.selectbox("Pilih Titik Sampling / Unit:", list_unit)

            g1, g2, g3 = st.columns(3)
            with g1:
                st.markdown("**Parameter Utama**")
                val_ph = st.number_input("pH Air", min_value=0.0, max_value=14.0, value=7.0, step=0.01)
                val_conduct = st.number_input("Conductivity (uS/cm)", min_value=0, value=500)
                val_tds = st.number_input("Total Dissolved Solid (TDS)", min_value=0, value=0)
                val_turb = st.number_input("Turbidity (NTU)", min_value=0.0, value=0.0)

            with g2:
                st.markdown("**Kandungan Alkalinitas & Mineral**")
                val_hard = st.number_input("Total Hardness (ppm)", min_value=0.0, value=0.0)
                val_m_alk = st.number_input("M-Alkalinity (ppm)", min_value=0.0, value=0.0)
                val_silica = st.number_input("Silica (ppm)", min_value=0.0, value=0.0)
                val_chlor = st.number_input("Chloride (ppm)", min_value=0.0, value=0.0)

            with g3:
                st.markdown("**Parameter Khusus Logam & Gas**")
                val_iron = st.number_input("Iron / Besi (ppm)", min_value=0.0, value=0.0, format="%.3f")
                val_phos = st.number_input("O-Phosphate (ppm)", min_value=0.0, value=0.0)
                val_sulfit = st.number_input("Sulfit (ppm)", min_value=0.0, value=0.0) if pilihan_modul == "BOILER" else 0.0
                val_lsi = st.number_input("LSI Index", value=0.0, step=0.01) if pilihan_modul == "COOLING TOWER" else 0.0

            st.divider()
            tombol_save = st.form_submit_button("🔒 Kunci & Simpan ke Excel GitHub", type="primary")

        if tombol_save:
            if not nama_teknisi:
                st.error(
                    "⚠️ Gagal Simpan! Anda **wajib memasukkan Nama Teknisi** "
                    "di menu sidebar sebelah kiri sebelum menyimpan data!"
                )
            else:
                with st.spinner("Sedang mengunggah data aman ke Excel GitHub..."):
                    data_baru = {
                        "ID_Data": f"WTP-{str(uuid.uuid4())[:5].upper()}",
                        "Teknisi": nama_teknisi,
                        "Plant": pilihan_plant,
                        "Modul": pilihan_modul,
                        "Unit_Titik": val_unit,
                        "Tanggal": str(tgl),
                        "pH": val_ph,
                        "Conduct": val_conduct,
                        "TDS": val_tds,
                        "Tot_Hardness": val_hard,
                        "M_Alkalinity": val_m_alk,
                        "Silica": val_silica,
                        "Chloride": val_chlor,
                        "Iron": val_iron,
                        "Turbidity": val_turb,
                        "O_Phosphate": val_phos,
                        "LSI": val_lsi,
                        "Sulfit": val_sulfit,
                    }
                    df_updated = pd.concat([df_data, pd.DataFrame([data_baru])], ignore_index=True)
                    if save_data_to_github(df_updated):
                        st.success(f"🎉 Sukses! Data lab {pilihan_modul} berhasil disimpan oleh {nama_teknisi}!")
                        st.cache_data.clear()
                        st.rerun()

    # =====================================================
    # TAB 2: LIVE DASHBOARD & TREN HISTORIS
    # =====================================================
    with tab_dash:
        df_filtered = df_data[(df_data["Plant"] == pilihan_plant) & (df_data["Modul"] == pilihan_modul)]

        if df_filtered.empty:
            st.info(
                f"Belum ada histori data untuk kategori {pilihan_modul} di {pilihan_plant}. "
                "Silakan isi form input terlebih dahulu!"
            )
        else:
            df_filtered = df_filtered.sort_values(by="Tanggal")

            st.subheader(f"📊 Live Dashboard Pemantauan Tren - {pilihan_modul} ({pilihan_plant})")
            render_trend_charts(df_filtered, pilihan_modul)

            with st.expander("👀 Lihat Lembar Kerja Log Data Mentah Master"):
                st.dataframe(df_filtered.drop(columns=["ID_Data"], errors="ignore"), use_container_width=True)

            st.divider()
            st.subheader("🔗 Bagikan Dashboard Tren Hari Ini")
            if st.button("Generate Link Bagikan", type="primary"):
                last_row = df_filtered.iloc[-1]
                unique_id = last_row["ID_Data"]
                # TODO: ganti base_url ini dengan URL Streamlit Cloud asli begitu sudah deploy
                base_url = "http://localhost:8501"
                share_url = f"{base_url}/?id={unique_id}"
                st.success("🎉 Link Berhasil Dibuat!")
                st.code(share_url, language="text")

    # =====================================================
    # TAB 3: KELOLA / EDIT / HAPUS DATA
    # =====================================================
    with tab_kelola:
        st.subheader("🛠️ Panel Koreksi Data Lab Master GitHub")

        if df_data.empty:
            st.info("Tidak ada data untuk dikelola.")
        else:
            pilihan_baris = [
                f"{row['Tanggal']} | {row['Plant']} | {row['Modul']} | {row['Unit_Titik']} | {row['ID_Data']}"
                for _, row in df_data.iterrows()
            ]
            data_terpilih = st.selectbox("Pilih Baris Data Lab yang Mau Diperbaiki:", pilihan_baris)
            selected_id = data_terpilih.split(" | ")[-1]
            filtered_rows = df_data[df_data["ID_Data"] == selected_id]

            if filtered_rows.empty:
                st.warning("Data tidak ditemukan, coba refresh halaman.")
            else:
                data_lama = filtered_rows.iloc[0]
                st.markdown("---")
                st.write(f"🔄 Silakan Ubah Nilai Koreksi untuk data milik Teknisi: {data_lama['Teknisi']}")

                e1, e2, e3 = st.columns(3)
                with e1:
                    edit_ph = st.number_input("Koreksi pH", min_value=0.0, max_value=14.0,
                                               value=float(data_lama["pH"]), step=0.01, key="e_ph")
                    edit_conduct = st.number_input("Koreksi Conductivity", min_value=0,
                                                    value=int(data_lama["Conduct"]), key="e_cond")
                    edit_tds = st.number_input("Koreksi TDS", min_value=0,
                                                value=int(data_lama["TDS"]), key="e_tds")
                    edit_turb = st.number_input("Koreksi Turbidity", min_value=0.0,
                                                 value=float(data_lama["Turbidity"]), key="e_turb")
                with e2:
                    edit_hard = st.number_input("Koreksi Tot. Hardness", min_value=0.0,
                                                 value=float(data_lama["Tot_Hardness"]), key="e_hard")
                    edit_m_alk = st.number_input("Koreksi M-Alkalinity", min_value=0.0,
                                                  value=float(data_lama["M_Alkalinity"]), key="e_malk")
                    edit_silica = st.number_input("Koreksi Silica", min_value=0.0,
                                                   value=float(data_lama["Silica"]), key="e_sil")
                    edit_chlor = st.number_input("Koreksi Chloride", min_value=0.0,
                                                  value=float(data_lama["Chloride"]), key="e_chlor")
                with e3:
                    edit_iron = st.number_input("Koreksi Iron", min_value=0.0,
                                                 value=float(data_lama["Iron"]), format="%.3f", key="e_iron")
                    edit_phos = st.number_input("Koreksi O-Phosphate", min_value=0.0,
                                                 value=float(data_lama["O_Phosphate"]), key="e_phos")
                    edit_sulfit = st.number_input("Koreksi Sulfit", min_value=0.0,
                                                   value=float(data_lama["Sulfit"]), key="e_sulf")
                    edit_lsi = st.number_input("Koreksi LSI", value=float(data_lama["LSI"]),
                                                step=0.01, key="e_lsi")

                btn_col1, btn_col2, _ = st.columns(3)
                with btn_col1:
                    if st.button("💾 Simpan Perubahan ke GitHub", type="primary"):
                        with st.spinner("Memperbarui database master..."):
                            idx = df_data[df_data["ID_Data"] == selected_id].index
                            df_data.loc[idx, "pH"] = edit_ph
                            df_data.loc[idx, "Conduct"] = edit_conduct
                            df_data.loc[idx, "TDS"] = edit_tds
                            df_data.loc[idx, "Turbidity"] = edit_turb
                            df_data.loc[idx, "Tot_Hardness"] = edit_hard
                            df_data.loc[idx, "M_Alkalinity"] = edit_m_alk
                            df_data.loc[idx, "Silica"] = edit_silica
                            df_data.loc[idx, "Chloride"] = edit_chlor
                            df_data.loc[idx, "Iron"] = edit_iron
                            df_data.loc[idx, "O_Phosphate"] = edit_phos
                            df_data.loc[idx, "Sulfit"] = edit_sulfit
                            df_data.loc[idx, "LSI"] = edit_lsi

                            if save_data_to_github(df_data):
                                st.success("👍 Database master di GitHub sukses diperbarui!")
                                st.cache_data.clear()
                                st.rerun()
                with btn_col2:
                    if st.button("🗑️ Hapus Baris Ini dari GitHub", type="secondary"):
                        with st.spinner("Menghapus baris..."):
                            df_after_delete = df_data[df_data["ID_Data"] != selected_id]
                            if save_data_to_github(df_after_delete):
                                st.warning("🗑️ Baris data telah terhapus dari file Excel GitHub.")
                                st.cache_data.clear()
                                st.rerun()
