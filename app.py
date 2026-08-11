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
st.set_page_config(page_title="WTP Treatment Master Dashboard", layout="wide", page_icon="💧")

# Ambil kredensial dari Streamlit Secrets
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    GITHUB_REPO = st.secrets["GITHUB_REPO"]
    FILE_PATH = "database_wtp_master.xlsx"
except Exception:
    st.error("❌ Token atau Nama Repo GitHub belum di-setting di Streamlit Secrets, bro!")
    st.stop()

MASTER_COLUMNS = [
    "ID_Data", "Teknisi", "Plant", "Modul", "Unit_Titik", "Tanggal",
    "pH", "Conduct", "TDS", "Cycle_TDS", "Tot_Hardness", "Cycle_Hardness",
    "P_Alkalinity", "M_Alkalinity", "Silica", "Cycle_Silika",
    "Chloride", "Cycle_Chloride", "Iron", "Turbidity", "O_Phosphate",
    "Sulfit", "Dissolved_Oxygen", "Bacteria_Count", "LSI", "Corr_Index",
]


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
            repo.update_file(FILE_PATH, "Update WTP Master Database via Web App", excel_data, sha)
        else:
            repo.create_file(FILE_PATH, "Inisialisasi WTP Master Database via Web App", excel_data)
        return True
    except Exception as e:
        st.error(f"Gagal push ke GitHub: {e}")
        return False


def safe_float(row, col, default=0.0):
    """Ambil nilai float dari row, fallback ke default kalau NaN/kosong."""
    val = row[col]
    return float(val) if pd.notna(val) else default


# =========================================================
# 3. FORM INPUT PER MODUL
# =========================================================
def render_boiler_form():
    """Form input khusus modul BOILER. Return dict nilai + unit terpilih."""
    val_unit = st.selectbox(
        "Pilih Titik Sampling Boiler:",
        ["Deaerator", "WHB Off Gass 1", "WHB Off Gass 2", "WHB Plant 1", "WHB Plant 2"],
    )
    g1, g2 = st.columns(2)
    with g1:
        val_ph = st.number_input("pH (Limit Deaerator: >6.5 | WHB: 10.5-11.0)",
                                  min_value=0.0, max_value=14.0, value=10.5, step=0.01)
        val_conduct = st.number_input("Conductivity uS/cm (Limit Deaerator: <300 | WHB: <1500)",
                                       min_value=0, value=1000)
        val_tds = st.number_input("Total Dissolved Solid / TDS (ppm)", min_value=0, value=500)
        val_hard = st.number_input("Total Hardness ppm (Limit Deaerator: <2 | WHB: Cycled)",
                                    min_value=0.0, value=0.0)
        val_m_alk = st.number_input("M-Alkalinity ppm (Limit Deaerator: <50 | WHB: <600)",
                                     min_value=0.0, value=150.0)
    with g2:
        val_silica = st.number_input("Silica ppm (Limit Deaerator: <2 | WHB: <150)", min_value=0.0, value=50.0)
        val_chlor = st.number_input("Chloride ppm (Limit Deaerator: <20 | WHB: <250)", min_value=0.0, value=40.0)
        val_iron = st.number_input("Iron / Besi ppm (Limit: <1)", min_value=0.0, value=0.05, format="%.3f")
        val_phos = st.number_input("O-Phosphate ppm (Limit WHB Plant: 2-10)", min_value=0.0, value=4.0)
        val_sulfit = st.number_input("Sulfit ppm (Limit WHB Plant: <150)", min_value=0.0, value=30.0)
        val_do = st.selectbox("Dissolved Oxygen (Limit: Trace)", ["Trace", "< 0.02", "High"])

    values = {
        "pH": val_ph, "Conduct": val_conduct, "TDS": val_tds, "Tot_Hardness": val_hard,
        "M_Alkalinity": val_m_alk, "Silica": val_silica, "Chloride": val_chlor, "Iron": val_iron,
        "Turbidity": 0.0, "O_Phosphate": val_phos, "Sulfit": val_sulfit, "Dissolved_Oxygen": val_do,
        "Bacteria_Count": 0, "LSI": 0.0, "Corr_Index": 0.0,
    }
    return val_unit, values


def render_cooling_tower_form():
    """Form input khusus modul COOLING TOWER. Return dict nilai + unit terpilih."""
    val_unit = st.selectbox("Pilih Titik Sampling Cooling Tower:", ["SBR", "Reject RO", "BP 1", "BP 2"])
    g1, g2 = st.columns(2)
    with g1:
        val_ph = st.number_input("pH (Limit SBR: >6.5 | BP: 8.0-8.5)",
                                  min_value=0.0, max_value=14.0, value=8.2, step=0.01)
        val_conduct = st.number_input("Conductivity uS/cm (Limit SBR: <300 | BP: <1500)",
                                       min_value=0, value=1100)
        val_hard = st.number_input("Total Hardness ppm (Limit SBR: <150 | BP: <600)", min_value=0.0, value=250.0)
        val_m_alk = st.number_input("M-Alkalinity ppm (Limit SBR: <150 | BP: <350)", min_value=0.0, value=200.0)
        val_silica = st.number_input("Silica ppm (Limit SBR: <50 | BP: <150)", min_value=0.0, value=100.0)
    with g2:
        val_chlor = st.number_input("Chloride ppm (Limit SBR: <50 | BP: <250)", min_value=0.0, value=120.0)
        val_iron = st.number_input("Iron / Besi ppm (Limit: <1)", min_value=0.0, value=0.02, format="%.3f")
        val_turb = st.number_input("Turbidity NTU (Limit SBR: <5 | BP: <20)", min_value=0.0, value=5.0)
        val_phos = st.number_input("O-Phosphate ppm (Limit BP: 5-10)", min_value=0.0, value=5.0)
        val_bacteria = st.number_input("A. Bacteria Count (Limit BP: 10.000 cfu/ml)", min_value=0, value=1000)
        val_lsi = st.number_input("LSI Index", value=1.0, step=0.01)

    values = {
        "pH": val_ph, "Conduct": val_conduct, "TDS": 0, "Tot_Hardness": val_hard,
        "M_Alkalinity": val_m_alk, "Silica": val_silica, "Chloride": val_chlor, "Iron": val_iron,
        "Turbidity": val_turb, "O_Phosphate": val_phos, "Sulfit": 0.0, "Dissolved_Oxygen": "Trace",
        "Bacteria_Count": val_bacteria, "LSI": val_lsi, "Corr_Index": 0.0,
    }
    return val_unit, values


def render_chiller_form():
    """Form input khusus modul CHILLER. Return dict nilai + unit terpilih."""
    val_unit = st.selectbox("Pilih Titik Sampling Chiller:", ["RO Chiller", "Chiller Tank"])
    g1, g2 = st.columns(2)
    with g1:
        val_ph = st.number_input("pH (Limit Range: 7.0 - 10.0)", min_value=0.0, max_value=14.0, value=7.5, step=0.01)
        val_conduct = st.number_input("Conductivity uS/cm (Limit RO: <50 | Tank: <2000)", min_value=0, value=600)
        val_hard = st.number_input("Total Hardness ppm (Limit RO: <15 | Tank: <300)", min_value=0.0, value=120.0)
        val_m_alk = st.number_input("M-Alkalinity ppm (Limit Tank: <500)", min_value=0.0, value=100.0)
    with g2:
        val_silica = st.number_input("Silica ppm (Limit RO: <15 | Tank: <150)", min_value=0.0, value=40.0)
        val_chlor = st.number_input("Chloride ppm (Limit RO: <10 | Tank: <150)", min_value=0.0, value=50.0)
        val_iron = st.number_input("Iron / Besi ppm (Limit RO: <0.1 | Tank: <1)",
                                    min_value=0.0, value=0.01, format="%.3f")
        val_turb = st.number_input("Turbidity NTU (Limit RO: <5 | Tank: <20)", min_value=0.0, value=2.0)
        val_corr = st.number_input("Corr. Index mpy (Limit Tank: <0.5)", min_value=0.0, value=0.05, step=0.01)

    values = {
        "pH": val_ph, "Conduct": val_conduct, "TDS": 0, "Tot_Hardness": val_hard,
        "M_Alkalinity": val_m_alk, "Silica": val_silica, "Chloride": val_chlor, "Iron": val_iron,
        "Turbidity": val_turb, "O_Phosphate": 0.0, "Sulfit": 0.0, "Dissolved_Oxygen": "Trace",
        "Bacteria_Count": 0, "LSI": 0.0, "Corr_Index": val_corr,
    }
    return val_unit, values


# =========================================================
# 4. RUMUS OTOMATIS CYCLE (BOILER WHB & COOLING TOWER BP)
# =========================================================
def calculate_cycle_values(df_data, plant, tanggal, modul, unit, values):
    """Hitung Cycle_TDS / Cycle_Hardness / Cycle_Silika / Cycle_Chloride
    berdasarkan data umpan (Deaerator untuk Boiler, SBR untuk Cooling Tower)."""
    cycle_tds = cycle_hard = cycle_silica = cycle_chlor = None

    df_ref = df_data[(df_data["Plant"] == plant) & (df_data["Tanggal"] == str(tanggal))]

    if modul == "BOILER" and "WHB" in unit:
        # Rumus Cycle TDS Boiler = TDS WHB / TDS Deaerator (Umpan)
        row_dea = df_ref[df_ref["Unit_Titik"] == "Deaerator"]
        if not row_dea.empty and float(row_dea.iloc[0]["TDS"]) > 0:
            cycle_tds = values["TDS"] / float(row_dea.iloc[0]["TDS"])

    elif modul == "COOLING TOWER" and "BP" in unit:
        # Rumus Cycle CT = Nilai Parameter BP / Nilai Parameter SBR (Umpan)
        row_sbr = df_ref[df_ref["Unit_Titik"] == "SBR"]
        if not row_sbr.empty:
            sbr_data = row_sbr.iloc[0]
            if float(sbr_data["Tot_Hardness"]) > 0:
                cycle_hard = values["Tot_Hardness"] / float(sbr_data["Tot_Hardness"])
            if float(sbr_data["Silica"]) > 0:
                cycle_silica = values["Silica"] / float(sbr_data["Silica"])
            if float(sbr_data["Chloride"]) > 0:
                cycle_chlor = values["Chloride"] / float(sbr_data["Chloride"])

    return cycle_tds, cycle_hard, cycle_silica, cycle_chlor


# =========================================================
# 5. DASHBOARD: GRAFIK TREN
# =========================================================
def render_trend_charts(df_filtered: pd.DataFrame, modul: str):
    cg1, cg2 = st.columns(2)
    with cg1:
        fig_ph = px.line(df_filtered, x="Tanggal", y="pH", color="Unit_Titik",
                          title="1. Grafik Tren Fluktuasi pH Air", markers=True)
        st.plotly_chart(fig_ph, use_container_width=True)
    with cg2:
        fig_cond = px.line(df_filtered, x="Tanggal", y="Conduct", color="Unit_Titik",
                            title="2. Grafik Tren Conductivity", markers=True)
        st.plotly_chart(fig_cond, use_container_width=True)

    cg3, cg4 = st.columns(2)
    with cg3:
        fig_hard = px.line(df_filtered, x="Tanggal", y="Tot_Hardness", color="Unit_Titik",
                            title="3. Grafik Tren Total Hardness", markers=True)
        st.plotly_chart(fig_hard, use_container_width=True)
    with cg4:
        fig_malk = px.line(df_filtered, x="Tanggal", y="M_Alkalinity", color="Unit_Titik",
                            title="4. Grafik Tren M-Alkalinity", markers=True)
        st.plotly_chart(fig_malk, use_container_width=True)

    cg5, cg6 = st.columns(2)
    with cg5:
        fig_sil = px.line(df_filtered, x="Tanggal", y="Silica", color="Unit_Titik",
                           title="5. Tren Kandungan Silica", markers=True)
        st.plotly_chart(fig_sil, use_container_width=True)
    with cg6:
        fig_chlor = px.line(df_filtered, x="Tanggal", y="Chloride", color="Unit_Titik",
                             title="6. Tren Korosivitas Chloride", markers=True)
        st.plotly_chart(fig_chlor, use_container_width=True)

    st.markdown("---")
    st.subheader("📈 Visualisasi Parameter Khusus Siklus & Indeks")
    cg7, cg8 = st.columns(2)
    with cg7:
        if modul == "BOILER":
            fig_spec = px.line(df_filtered, x="Tanggal", y="Sulfit", color="Unit_Titik",
                                title="7. Grafik Parameter Khusus: Kadar Sulfit (ppm)", markers=True)
        elif modul == "COOLING TOWER":
            fig_spec = px.line(df_filtered, x="Tanggal", y="Cycle_Hardness", color="Unit_Titik",
                                title="7. Grafik Parameter Khusus: Cycle Hardness (Rumus Otomatis)", markers=True)
        else:
            fig_spec = px.bar(df_filtered, x="Tanggal", y="Corr_Index", color="Unit_Titik",
                               title="7. Grafik Parameter Khusus: Corrosion Index (mpy)")
        st.plotly_chart(fig_spec, use_container_width=True)
    with cg8:
        if modul == "BOILER":
            fig_spec2 = px.line(df_filtered, x="Tanggal", y="Cycle_TDS", color="Unit_Titik",
                                 title="8. Grafik Rumus Otomatis: Cycle TDS", markers=True)
        elif modul == "COOLING TOWER":
            fig_spec2 = px.bar(df_filtered, x="Tanggal", y="LSI", color="Unit_Titik",
                                title="8. Grafik Indeks Kejenuhan Air Langelier (LSI Index)", barmode="group")
        else:
            fig_spec2 = px.line(df_filtered, x="Tanggal", y="Turbidity", color="Unit_Titik",
                                 title="8. Grafik Tren Turbidity NTU", markers=True)
        st.plotly_chart(fig_spec2, use_container_width=True)


# =========================================================
# 6. LOAD DATA & ROUTING HALAMAN (SHARE LINK vs MAIN APP)
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
        st.dataframe(df_shared.dropna(axis=1, how="all"), use_container_width=True)

        if st.button("⬅️ Buka Aplikasi Utama"):
            st.query_params.clear()
            st.rerun()

else:
    # -----------------------------------------------------
    # HALAMAN: UTAMA (INPUT, LIVE DASHBOARD, EDIT)
    # -----------------------------------------------------
    st.title("🏭 WTP Treatment Quality Control & Monitoring Master System")

    st.sidebar.markdown("### 🧑‍💻 Personel & Lokasi")
    nama_teknisi = st.sidebar.text_input("Nama Teknisi / Surveyor (Wajib)", placeholder="Ketik nama Anda...")
    pilihan_plant = st.sidebar.selectbox("Pilih Wilayah Kerja (Plant):", ["Plant A", "Plant B"])
    pilihan_modul = st.sidebar.selectbox("Pilih Modul Monitoring:", ["BOILER", "COOLING TOWER", "CHILLER"])

    tab_form, tab_dash, tab_kelola = st.tabs(
        ["📝 Form Input Lab Dinamis", "📊 Dashboard Analisis & Share", "⚙️ Kelola / Edit Data"]
    )

    # =====================================================
    # TAB 1: FORM INPUT UTAMA (DINAMIS PER MODUL)
    # =====================================================
    with tab_form:
        st.subheader(f"Formulir Input Khusus - UNIT {pilihan_modul} [{pilihan_plant}]")

        with st.form("master_wtp_form", clear_on_submit=True):
            tgl = st.date_input("Tanggal Sampling", datetime.date.today())

            if pilihan_modul == "BOILER":
                val_unit, form_values = render_boiler_form()
            elif pilihan_modul == "COOLING TOWER":
                val_unit, form_values = render_cooling_tower_form()
            else:
                val_unit, form_values = render_chiller_form()

            st.divider()
            st.caption(
                "💡 Catatan: Parameter seperti 'Cycle Hardness', 'Cycle TDS', 'Cycle Silika', "
                "dan 'Cycle Chloride' akan otomatis dihitung secara akurat oleh rumus sistem komputer."
            )
            tombol_save = st.form_submit_button("🔒 Kunci & Kirim ke Excel GitHub", type="primary")

        if tombol_save:
            if not nama_teknisi:
                st.error(
                    "⚠️ Gagal Simpan! Anda wajib memasukkan Nama Teknisi "
                    "di menu sidebar sebelah kiri sebelum mengklik simpan!"
                )
            else:
                with st.spinner("Sedang memproses perhitungan rumus otomatis..."):
                    cycle_tds, cycle_hard, cycle_silica, cycle_chlor = calculate_cycle_values(
                        df_data, pilihan_plant, tgl, pilihan_modul, val_unit, form_values
                    )

                    data_baru = {
                        "ID_Data": f"WTP-{str(uuid.uuid4())[:5].upper()}",
                        "Teknisi": nama_teknisi,
                        "Plant": pilihan_plant,
                        "Modul": pilihan_modul,
                        "Unit_Titik": val_unit,
                        "Tanggal": str(tgl),
                        "pH": form_values["pH"],
                        "Conduct": form_values["Conduct"],
                        "TDS": form_values["TDS"],
                        "Cycle_TDS": cycle_tds,
                        "Tot_Hardness": form_values["Tot_Hardness"],
                        "Cycle_Hardness": cycle_hard,
                        "P_Alkalinity": 0.0,
                        "M_Alkalinity": form_values["M_Alkalinity"],
                        "Silica": form_values["Silica"],
                        "Cycle_Silika": cycle_silica,
                        "Chloride": form_values["Chloride"],
                        "Cycle_Chloride": cycle_chlor,
                        "Iron": form_values["Iron"],
                        "Turbidity": form_values["Turbidity"],
                        "O_Phosphate": form_values["O_Phosphate"],
                        "Sulfit": form_values["Sulfit"],
                        "Dissolved_Oxygen": form_values["Dissolved_Oxygen"],
                        "Bacteria_Count": form_values["Bacteria_Count"],
                        "LSI": form_values["LSI"],
                        "Corr_Index": form_values["Corr_Index"],
                    }
                    df_updated = pd.concat([df_data, pd.DataFrame([data_baru])], ignore_index=True)
                    if save_data_to_github(df_updated):
                        st.success("🎉 Sukses! Data lab berhasil direkam dan rumus kalkulasi otomatis telah sukses dijalankan!")
                        st.cache_data.clear()
                        st.rerun()

    # =====================================================
    # TAB 2: LIVE DASHBOARD
    # =====================================================
    with tab_dash:
        df_filtered = df_data[(df_data["Plant"] == pilihan_plant) & (df_data["Modul"] == pilihan_modul)]

        if df_filtered.empty:
            st.info(f"Belum ada histori data untuk kategori {pilihan_modul} di {pilihan_plant}.")
        else:
            df_filtered = df_filtered.sort_values(by="Tanggal")
            st.subheader(f"📊 Dashboard Analisis Tren Unit {pilihan_modul} - {pilihan_plant}")
            render_trend_charts(df_filtered, pilihan_modul)

            with st.expander("👀 Lihat Lembar Kerja Log Tabel Master Sesuai Filter"):
                st.dataframe(df_filtered.dropna(axis=1, how="all"), use_container_width=True)

            st.divider()
            if st.button("Generate Link Bagikan Dashboard", type="primary"):
                unique_id = df_filtered.iloc[-1]["ID_Data"]
                base_url = "http://localhost:8501"
                share_url = f"{base_url}/?id={unique_id}"
                st.success("🎉 Link Berhasil Dibuat!")
                st.code(share_url, language="text")

    # =====================================================
    # TAB 3: KELOLA / EDIT / HAPUS DATA
    # =====================================================
    with tab_kelola:
        st.subheader("🛠️ Panel Perbaikan Data Master WTP")

        if df_data.empty:
            st.info("Tidak ada data untuk diedit.")
        else:
            pilihan_baris = [
                f"{row['Tanggal']} | {row['Plant']} | {row['Modul']} | {row['Unit_Titik']} | {row['ID_Data']}"
                for _, row in df_data.iterrows()
            ]
            data_terpilih = st.selectbox("Pilih Baris Data Lab yang Mau Diperbaiki:", pilihan_baris)
            selected_id = data_terpilih.split(" | ")[-1]
            filtered_rows = df_data[df_data["ID_Data"] == selected_id]

            if filtered_rows.empty:
                st.warning("Data tidak ditemukan.")
            else:
                data_lama = filtered_rows.iloc[0]
                st.markdown("---")
                st.write(f"🔄 Silakan Ubah Koreksi Nilai untuk Unit {data_lama['Unit_Titik']}")

                e1, e2, e3 = st.columns(3)
                with e1:
                    edit_ph = st.number_input("Koreksi pH", min_value=0.0, max_value=14.0,
                                               value=float(data_lama["pH"]), step=0.01, key="e_ph")
                    edit_conduct = st.number_input("Koreksi Conductivity", min_value=0,
                                                    value=int(data_lama["Conduct"]), key="e_cond")
                    edit_tds = st.number_input("Koreksi TDS", min_value=0,
                                                value=int(safe_float(data_lama, "TDS")), key="e_tds")
                    edit_turb = st.number_input("Koreksi Turbidity", min_value=0.0,
                                                 value=safe_float(data_lama, "Turbidity"), key="e_turb")
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
                                                 value=safe_float(data_lama, "O_Phosphate"), key="e_phos")
                    edit_sulfit = st.number_input("Koreksi Sulfit", min_value=0.0,
                                                   value=safe_float(data_lama, "Sulfit"), key="e_sulf")
                    edit_lsi = st.number_input("Koreksi LSI", value=safe_float(data_lama, "LSI"),
                                                step=0.01, key="e_lsi")
                    edit_corr = st.number_input("Koreksi Corr. Index", value=safe_float(data_lama, "Corr_Index"),
                                                 step=0.01, key="e_corr")

                btn_col1, btn_col2, _ = st.columns(3)
                with btn_col1:
                    if st.button("💾 Simpan Perubahan ke GitHub", type="primary"):
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
                        df_data.loc[idx, "Corr_Index"] = edit_corr

                        if save_data_to_github(df_data):
                            st.success("👍 File Excel di GitHub sukses diperbarui!")
                            st.cache_data.clear()
                            st.rerun()
                with btn_col2:
                    if st.button("🗑️ Hapus Baris Ini dari GitHub", type="secondary"):
                        df_after_delete = df_data[df_data["ID_Data"] != selected_id]
                        if save_data_to_github(df_after_delete):
                            st.warning("🗑️ Baris data telah terhapus dari file Excel GitHub.")
                            st.cache_data.clear()
                            st.rerun()
