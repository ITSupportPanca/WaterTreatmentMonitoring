import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import uuid
import io
from github import Github

# --- 1. CONFIG UTAMA WEBSITE ---
st.set_page_config(page_title="Water Treatment Monitoring", layout="wide", page_icon="💧")

# Ambil kredensial dari Streamlit Secrets
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    GITHUB_REPO = st.secrets["GITHUB_REPO"]
    FILE_PATH = "database.xlsx"
except Exception:
    st.error("❌ Token atau Nama Repo GitHub belum di-setting di Streamlit Secrets, bro!")
    st.stop()

# --- FUNGSI UNTUK MEMBACA DATA DARI EXCEL GITHUB ---
@st.cache_data(ttl=5)  # Cache disegarkan setiap 5 detik agar real-time
def load_data_from_github():
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)
        file_content = repo.get_contents(FILE_PATH)
        data_bytes = file_content.decoded_content
        df = pd.read_excel(io.BytesIO(data_bytes))
        return df, file_content.sha
    except Exception:
        # Jika file belum ada di GitHub, buat dataframe kosong awal
        df_init = pd.DataFrame(columns=[
            "ID_Data", "Tanggal", "pH", "Conduct", "Tot_Hardness", "Cycle_Hard",
            "P_Alkalinity", "M_Alkalinity", "Silica", "Cycle_Silika", 
            "Chloride", "Cycle_Chloride", "Iron", "Turbidity", "O_Phosphate", "LSI"
        ])
        return df_init, None

# --- FUNGSI UNTUK MENYIMPAN/PUSH DATA BALIK KE EXCEL GITHUB ---
def save_data_to_github(df):
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)
        
        # Mengubah dataframe kembali menjadi file excel di memori
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        excel_data = output.getvalue()
        
        # Cek apakah file sudah ada untuk menentukan apakah Overwrite atau Create New
        _, sha = load_data_from_github()
        
        if sha:
            repo.update_file(FILE_PATH, "Update database monitoring air via Web App", excel_data, sha)
        else:
            repo.create_file(FILE_PATH, "Inisialisasi database monitoring air via Web App", excel_data)
        return True
    except Exception as e:
        st.error(f"Gagal push ke GitHub: {e}")
        return False

# Load data aktif saat ini
df_data, _ = load_data_from_github()

# Ambil ID Share jika diakses melalui link bagikan
query_params = st.query_params

# --- 2. LOGIKA HALAMAN: LINK SHARE (VIEW ONLY) ---
if "id" in query_params:
    share_id = query_params["id"]
    df_shared = df_data[df_data["ID_Data"] == share_id]
    
    if not df_shared.empty:
        st.title("💧 Shared Dashboard - Water Treatment Monitoring")
        st.info("👀 Mode: Lihat Saja (View-Only).")
        
        c1, c2 = st.columns(2)
        with c1:
            fig1 = px.line(df_data, x="Tanggal", y=["pH", "LSI"], title="Tren Kestabilan Air (pH vs LSI)", markers=True)
            st.plotly_chart(fig1, use_container_width=True)
        with c2:
            fig2 = px.line(df_data, x="Tanggal", y="Silica", title="Tren Kandungan Silica (ppm)", markers=True)
            st.plotly_chart(fig2, use_container_width=True)
            
        st.markdown("### 📋 Tabel Data Pemantauan")
        st.dataframe(df_shared.drop(columns=["ID_Data"], errors="ignore"), use_container_width=True)
        
        if st.button("⬅️ Buka Aplikasi Utama (Form Input)"):
            st.query_params.clear()
            st.rerun()
    else:
        st.error("❌ Link tidak valid atau data tidak ditemukan.")

# --- 3. LOGIKA HALAMAN: UTAMA (INPUT, LIVE DASHBOARD, EDIT) ---
else:
    st.title("💧 Water Treatment Quality Control & Monitoring System (Permanen GitHub Excel)")
    st.write("Semua data yang di-input dan di-edit di sini otomatis tersimpan permanen jadi file Excel di GitHub lu.")
    
    tab_form, tab_dash, tab_kelola = st.tabs(["📝 Form Input Lab Harian", "📊 Dashboard Analisis & Share", "⚙️ Kelola / Edit Data"])
    
    # --- TAB 1: FORM INPUT ---
    with tab_form:
        st.subheader("Form Input Parameter Air")
        with st.form("water_form", clear_on_submit=True):
            tgl = st.date_input("Tanggal Sampling", datetime.date.today())
            g1, g2, g3 = st.columns(3)
            
            with g1:
                st.markdown("**Kondisi Fisik & Utama**")
                val_ph = st.number_input("pH", min_value=0.0, max_value=14.0, value=7.0, step=0.01)
                val_conduct = st.number_input("Conductivity (Conduct)", min_value=0, value=1000)
                val_turb = st.number_input("Turbidity", min_value=0.0, value=0.0)
                val_lsi = st.number_input("LSI", value=0.0, step=0.01)
            
            with g2:
                st.markdown("**Kandungan Kimia & Hardness**")
                val_hard = st.number_input("Tot. Hardness", min_value=0.0, value=0.0)
                val_cyc_hard = st.number_input("Cycle Hard", min_value=0.0, value=0.0)
                val_p_alk = st.number_input("P-Alkalinity", min_value=0.0, value=0.0)
                val_m_alk = st.number_input("M-Alkalinity", min_value=0.0, value=0.0)
            
            with g3:
                st.markdown("**Silica, Chloride & Mineral**")
                val_silica = st.number_input("Silica", min_value=0.0, value=0.0)
                val_cyc_sil = st.number_input("Cycle Silika", min_value=0.0, value=0.0)
                val_chlor = st.number_input("Chloride", min_value=0.0, value=0.0)
                val_cyc_chl = st.number_input("Cycle Chloride", min_value=0.0, value=0.0)
                val_iron = st.number_input("Iron (Besi)", min_value=0.0, value=0.0, format="%.3f")
                val_phos = st.number_input("O-Phosphate", min_value=0.0, value=0.0)
                
            st.divider()
            tombol_save = st.form_submit_button("Simpan Data Lab Permanen", type="primary")
            
        if tombol_save:
            with st.spinner("Sedang mengunggah dan mengunci data ke Excel GitHub..."):
                data_baru = {
                    "ID_Data": f"WTM-{str(uuid.uuid4())[:5].upper()}",
                    "Tanggal": str(tgl),
                    "pH": val_ph,
                    "Conduct": val_conduct,
                    "Tot_Hardness": val_hard,
                    "Cycle_Hard": val_cyc_hard if val_cyc_hard > 0 else None,
                    "P_Alkalinity": val_p_alk,
                    "M_Alkalinity": val_m_alk,
                    "Silica": val_silica,
                    "Cycle_Silika": val_cyc_sil if val_cyc_sil > 0 else None,
                    "Chloride": val_chlor,
                    "Cycle_Chloride": val_cyc_chl if val_cyc_chl > 0 else None,
                    "Iron": val_iron,
                    "Turbidity": val_turb,
                    "O_Phosphate": val_phos,
                    "LSI": val_lsi
                }
                df_updated = pd.concat([df_data, pd.DataFrame([data_baru])], ignore_index=True)
                if save_data_to_github(df_updated):
                    st.success(f"🎉 Sukses! Data tanggal {tgl} terkunci permanen di database.xlsx GitHub!")
                    st.cache_data.clear()
                    st.rerun()

    # --- TAB 2: DASHBOARD & SHARE LINK ---
    with tab_dash:
        if df_data.empty:
            st.info("Belum ada data di database.xlsx GitHub lu bro. Silakan isi form input dulu!")
        else:
            df_data = df_data.sort_values(by="Tanggal")
            st.subheader("📋 Ringkasan Parameter Kritis Hari Ini")
            
            last_row = df

    # --- TAB 2: DASHBOARD & SHARE LINK ---
    with tab_dash:
        if df_data.empty:
            st.info("Belum ada data di database.xlsx GitHub lu bro. Silakan isi form input dulu!")
        else:
            df_data = df_data.sort_values(by="Tanggal")
            st.subheader("📋 Ringkasan Parameter Kritis Hari Ini")
            
            last_row = df_data.iloc[-1]
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("pH Terakhir", f"{last_row['pH']}")
            k2.metric("Conductivity", f"{int(last_row['Conduct'])} µS/cm")
            k3.metric("Silica Level", f"{last_row['Silica']} ppm")
            k4.metric("Nilai LSI", f"{last_row['LSI']}")
            
            st.divider()
            st.subheader("📈 Tren Grafik Analitik")
            cg1, cg2 = st.columns(2)
            with cg1:
                fig_ph = px.line(df_data, x="Tanggal", y="pH", title="Grafik Fluktuasi pH Air", markers=True)
                st.plotly_chart(fig_ph, use_container_width=True)
            with cg2:
                fig_sil = px.line(df_data, x="Tanggal", y="Silica", title="Tren Akumulasi Silica (ppm)", markers=True)
                st.plotly_chart(fig_sil, use_container_width=True)
                
            with st.expander("👀 Lihat Lembar Kerja Log Lengkap"):
                st.dataframe(df_data.drop(columns=["ID_Data"], errors="ignore"), use_container_width=True)
                
            st.divider()
            st.subheader("🔗 Bagikan Dashboard ini ke Orang Lain")
            if st.button("Generate Link Bagikan", type="primary"):
                unique_id = last_row["ID_Data"]
                base_url = "https://pkr-wt.streamlit.app/"  # ganti dengan URL Streamlit Cloud asli
                share_url = f"{base_url}/?id={unique_id}"
                st.success("🎉 Link Berhasil Dibuat!")
                st.code(share_url, language="text")

    # --- TAB 3: FITUR KELOLA DATA (EDIT & DELETE) ---
    with tab_kelola:
        st.subheader("🛠️ Panel Perbaikan Data Excel GitHub")
        if df_data.empty:
            st.info("Tidak ada data untuk diedit.")
        else:
            pilihan_baris = [f"{row['Tanggal']} | {row['ID_Data']}" for _, row in df_data.iterrows()]
            data_terpilih = st.selectbox("Pilih Baris Data yang Mau Diperbaiki:", pilihan_baris)
            selected_id = data_terpilih.split(" | ")[1]
            
            data_lama = df_data[df_data["ID_Data"] == selected_id].iloc[0]
            
            st.markdown("---")
            st.write(f"🔄 **Silakan Ubah Nilai untuk Data Tanggal: {data_lama['Tanggal']}**")
            
            e1, e2, e3 = st.columns(3)
            with e1:
                edit_ph = st.number_input("Ubah pH", min_value=0.0, max_value=14.0, value=float(data_lama["pH"]), step=0.01, key="e_ph")
                edit_conduct = st.number_input("Ubah Conductivity", min_value=0, value=int(data_lama["Conduct"]), key="e_cond")
                edit_turb = st.number_input("Ubah Turbidity", min_value=0.0, value=float(data_lama["Turbidity"]), key="e_turb")
                edit_lsi = st.number_input("Ubah LSI", value=float(data_lama["LSI"]), step=0.01, key="e_lsi")
            
            with e2:
                edit_hard = st.number_input("Ubah Tot. Hardness", min_value=0.0, value=float(data_lama["Tot_Hardness"]), key="e_hard")
                edit_cyc_hard = st.number_input("Ubah Cycle Hard", min_value=0.0, value=float(data_lama["Cycle_Hard"] if pd.notna(data_lama["Cycle_Hard"]) else 0.0), key="e_chard")
                edit_p_alk = st.number_input("Ubah P-Alkalinity", min_value=0.0, value=float(data_lama["P_Alkalinity"]), key="e_palk")
                edit_m_alk = st.number_input("Ubah M-Alkalinity", min_value=0.0, value=float(data_lama["M_Alkalinity"]), key="e_malk")
            
            with e3:
                edit_silica = st.number_input("Ubah Silica", min_value=0.0, value=float(data_lama["Silica"]), key="e_sil")
                edit_cyc_sil = st.number_input("Ubah Cycle Silika", min_value=0.0, value=float(data_lama["Cycle_Silika"] if pd.notna(data_lama["Cycle_Silika"]) else 0.0), key="e_csil")
                edit_chlor = st.number_input("Ubah Chloride", min_value=0.0, value=float(data_lama["Chloride"]), key="e_chlor")
                edit_cyc_chl = st.number_input("Ubah Cycle Chloride", min_value=0.0, value=float(data_lama["Cycle_Chloride"] if pd.notna(data_lama["Cycle_Chloride"]) else 0.0), key="e_cchlor")
                edit_iron = st.number_input("Ubah Iron", min_value=0.0, value=float(data_lama["Iron"]), format="%.3f", key="e_iron")
                edit_phos = st.number_input("Ubah O-Phosphate", min_value=0.0, value=float(data_lama["O_Phosphate"]), key="e_phos")
            
            btn_col1, btn_col2, _ = st.columns(3)
            with btn_col1:
                if st.button("💾 Simpan Perubahan ke GitHub", type="primary"):
                    with st.spinner("Memperbarui file Excel di GitHub..."):
                        idx = df_data[df_data["ID_Data"] == selected_id].index[0]
                        df_data.at[idx, "pH"] = edit_ph
                        df_data.at[idx, "Conduct"] = edit_conduct
                        df_data.at[idx, "Turbidity"] = edit_turb
                        df_data.at[idx, "LSI"] = edit_lsi
                        df_data.at[idx, "Tot_Hardness"] = edit_hard
                        df_data.at[idx, "Cycle_Hard"] = edit_cyc_hard if edit_cyc_hard > 0 else None
                        df_data.at[idx, "P_Alkalinity"] = edit_p_alk
                        df_data.at[idx, "M_Alkalinity"] = edit_m_alk
                        df_data.at[idx, "Silica"] = edit_silica
                        df_data.at[idx, "Cycle_Silika"] = edit_cyc_sil if edit_cyc_sil > 0 else None
                        df_data.at[idx, "Chloride"] = edit_chlor
                        df_data.at[idx, "Cycle_Chloride"] = edit_cyc_chl if edit_cyc_chl > 0 else None
                        df_data.at[idx, "Iron"] = edit_iron
                        df_data.at[idx, "O_Phosphate"] = edit_phos
                        
                        if save_data_to_github(df_data):
                            st.success("👍 File Excel di GitHub sukses diperbarui!")
                            st.cache_data.clear()
                            st.rerun()
            
            with btn_col2:
                if st.button("🗑️ Hapus Baris Ini dari GitHub", type="secondary"):
                    with st.spinner("Menghapus baris dari Excel GitHub..."):
                        df_filtered = df_data[df_data["ID_Data"] != selected_id]
                        if save_data_to_github(df_filtered):
                            st.warning("🗑️ Baris data telah terhapus dari file Excel GitHub.")
                            st.cache_data.clear()
                            st.rerun()
