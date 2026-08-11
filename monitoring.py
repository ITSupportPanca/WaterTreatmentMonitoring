import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import uuid

# --- 1. CONFIG UTAMA WEBSITE ---
st.set_page_config(page_title="Water Treatment Monitoring", layout="wide", page_icon="💧")

# Inisialisasi Database Simulasi di Memori Server (Gratisan)
if "db_water_monitoring" not in st.session_state:
    # Memasukkan data sampel awal berdasarkan foto Excel lu agar dashboard langsung muncul grafik
    st.session_state["db_water_monitoring"] = pd.DataFrame([
        {
            "Tanggal": "2026-06-02", "pH": 8.47, "Conduct": 1209, "Tot_Hardness": 301.2, "Cycle_Hard": None,
            "P_Alkalinity": 8.0, "M_Alkalinity": 240.0, "Silica": 85.0, "Cycle_Silika": None, 
            "Chloride": 140.0, "Cycle_Chloride": None, "Iron": 0.01, "Turbidity": 3.0, "O_Phosphate": 5.0, "LSI": 1.3
        },
        {
            "Tanggal": "2026-06-09", "pH": 8.34, "Conduct": 1069, "Tot_Hardness": 284.0, "Cycle_Hard": None,
            "P_Alkalinity": 10.0, "M_Alkalinity": 240.0, "Silica": 245.1, "Cycle_Silika": None, 
            "Chloride": 120.0, "Cycle_Chloride": None, "Iron": 0.01, "Turbidity": 2.0, "O_Phosphate": 5.0, "LSI": 1.2
        },
        {
            "Tanggal": "2026-08-04", "pH": 8.46, "Conduct": 841, "Tot_Hardness": 240.0, "Cycle_Hard": 1.2,
            "P_Alkalinity": 36.0, "M_Alkalinity": 84.0, "Silica": 309.8, "Cycle_Silika": 1.4, 
            "Chloride": 84.0, "Cycle_Chloride": 1.2, "Iron": 0.08, "Turbidity": 2.0, "O_Phosphate": 5.0, "LSI": 0.84
        }
    ])

if "db_shared_water" not in st.session_state:
    st.session_state["db_shared_water"] = {}

# Ambil ID Share jika diakses melalui link bagikan
query_params = st.query_params

# --- 2. LOGIKA HALAMAN: LINK SHARE (VIEW ONLY) ---
if "id" in query_params:
    share_id = query_params["id"]
    if share_id in st.session_state["db_shared_water"]:
        df_shared = st.session_state["db_shared_water"][share_id]
        
        st.title("💧 Shared Dashboard - Water Treatment Monitoring")
        st.info("👀 Mode: Lihat Saja (View-Only). Data dikunci saat link ini dibuat.")
        
        # Tampilkan visualisasi utama untuk penerima link share
        c1, c2 = st.columns(2)
        with c1:
            fig1 = px.line(df_shared, x="Tanggal", y=["pH", "LSI"], title="Tren Kestabilan Air (pH vs LSI)", markers=True)
            st.plotly_chart(fig1, use_container_width=True)
        with c2:
            fig2 = px.line(df_shared, x="Tanggal", y="Silica", title="Tren Kandungan Silica (ppm)", markers=True)
            st.plotly_chart(fig2, use_container_width=True)
            
        st.markdown("### 📋 Tabel Data Pemantauan")
        st.dataframe(df_shared, use_container_width=True)
        
        if st.button("⬅️ Buka Aplikasi Utama (Form Input)"):
            st.query_params.clear()
            st.rerun()
    else:
        st.error("❌ Link tidak valid atau data sudah dihapus.")
        if st.button("Kembali"):
            st.query_params.clear()
            st.rerun()

# --- 3. LOGIKA HALAMAN: UTAMA (INPUT & LIVE DASHBOARD) ---
else:
    st.title("💧 Water Treatment Quality Control & Monitoring System")
    st.write("Input hasil pengecekan laboratorium harian di bawah untuk memperbarui dashboard secara otomatis.")
    
    tab_form, tab_dash = st.tabs(["📝 Form Input Lab Harian", "📊 Dashboard Analisis & Share"])
    
    # --- TAB FORM INPUT ---
    with tab_form:
        st.subheader("Form Input Parameter Air")
        
        with st.form("water_form", clear_on_submit=True):
            # Input Dasar
            tgl = st.date_input("Tanggal Sampling", datetime.date.today())
            
            # Pengelompokan field agar form rapi (3 kolom ke samping)
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
            tombol_save = st.form_submit_button("Simpan Data Lab", type="primary")
            
        if tombol_save:
            # Memasukkan baris data ke database internal
            data_baru = {
                "Tanggal": str(tgl), "pH": val_ph, "Conduct": val_conduct, "Tot_Hardness": val_hard, "Cycle_Hard": val_cyc_hard if val_cyc_hard > 0 else None,
                "P_Alkalinity": val_p_alk, "M_Alkalinity": val_m_alk, "Silica": val_silica, "Cycle_Silika": val_cyc_sil if val_cyc_sil > 0 else None,
                "Chloride": val_chlor, "Cycle_Chloride": val_cyc_chl if val_cyc_chl > 0 else None, "Iron": val_iron, "Turbidity": val_turb, 
                "O_Phosphate": val_phos, "LSI": val_lsi
            }
            df_curr = st.session_state["db_water_monitoring"]
            st.session_state["db_water_monitoring"] = pd.concat([df_curr, pd.DataFrame([data_baru])], ignore_index=True)
            st.success(f"🎉 Data monitoring tanggal {tgl} sukses dimasukkan ke database!")
            st.balloons()

    # --- TAB DASHBOARD & SHARE LINK ---
    with tab_dash:
        df_data = st.session_state["db_water_monitoring"]
        
        # Urutkan berdasarkan tanggal terbaru agar rapi
        df_data = df_data.sort_values(by="Tanggal")
        
        st.subheader("📋 Ringkasan Parameter Kritis Hari Ini")
        
        # Ambil data baris terakhir untuk dijadikan Highlight Card
        last_row = df_data.iloc[-1]
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("pH Terakhir", f"{last_row['pH']}", delta="Normal" if 7 <= last_row['pH'] <= 8.5 else "Perlu Dicek")
        k2.metric("Conductivity", f"{int(last_row['Conduct'])} µS/cm")
        k3.metric("Silica Level", f"{last_row['Silica']} ppm")
        k4.metric("Nilai LSI", f"{last_row['LSI']}")
        
        st.divider()
        st.subheader("📈 Tren Grafik Analitik")
        
        # Baris Grafik 1
        cg1, cg2 = st.columns(2)
        with cg1:
            fig_ph = px.line(df_data, x="Tanggal", y="pH", title="Grafik Fluktuasi pH Air", markers=True, color_discrete_sequence=["#1f77b4"])
            st.plotly_chart(fig_ph, use_container_width=True)
        with cg2:
            fig_sil = px.line(df_data, x="Tanggal", y="Silica", title="Tren Akumulasi Silica (ppm)", markers=True, color_discrete_sequence=["#ff7f0e"])
            st.plotly_chart(fig_sil, use_container_width=True)
            
        # Baris Grafik 2
        cg3, cg4 = st.columns(2)
        with cg3:
            fig_cond = px.line(df_data, x="Tanggal", y="Conduct", title="Grafik Batas Conductivity", markers=True, color_discrete_sequence=["#2ca02c"])
            st.plotly_chart(fig_cond, use_container_width=True)
        with cg4:
            fig_lsi = px.bar(df_data, x="Tanggal", y="LSI", title="Indeks Kejenuhan Air (LSI)", color="LSI")
            st.plotly_chart(fig_lsi, use_container_width=True)
            
        # Tampilkan Seluruh Data Mentah
        with st.expander("👀 Lihat Lembar Kerja Log Lengkap (Format Tabel Excel)"):
            st.dataframe(df_data, use_container_width=True)
            
        # PROSES PEMBUATAN LINK UNTUK DI-SHARE
        st.divider()
        st.subheader("🔗 Bagikan Dashboard ini ke Orang Lain")
        if st.button("Generate Link Bagikan", type="primary"):
            unique_id = str(uuid.uuid4())[:8]
            # Kunci kondisi data saat ini untuk disimpan ke database link share
            st.session_state["db_shared_water"][unique_id] = df_data.copy()
            
            base_url = "http://localhost:8501"  # Nanti diganti link web asli pas udah di-onlinekan gratis
            share_url = f"{base_url}/?id={unique_id}"
            
            st.success("🎉 Link Berhasil Dibuat!")
            st.code(share_url, language="text")
            st.caption("Salin link di atas lalu kirim ke WhatsApp tim atau atasan lu agar mereka bisa pantau grafiknya.")
