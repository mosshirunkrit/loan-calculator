import pandas as pd
import numpy_financial as npf
import streamlit as st
from datetime import date, timedelta
import plotly.express as px

st.set_page_config(page_title="วางแผนชำระหนี้สินเชื่อ", page_icon="💰", layout="centered")

# ตั้งค่าฟอนต์ Prompt ทั้งหน้าเว็บ
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;500;600;700&display=swap');

    * {
        font-family: 'Sarabun', sans-serif !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <style>
    /* บังคับเปลี่ยนพื้นหลังแอปพลิเคชันให้ไล่สีเขียวมิ้นท์พาสเทล */
    [data-testid="stAppViewContainer"] {
        background-image: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 50%, #bbf7d0 100%) !important;
        background-attachment: fixed !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h2 style="font-size: 20px; font-weight: bold;">💰 วางแผนผ่อนชำระสินเชื่อ ทุ่งหว้า🔥</h2>', unsafe_allow_html=True)
st.write("เครื่องมือคำนวณและวางแผนชำระหนี้รายเดือน")

# --- ฟังก์ชันช่วยแปลง ค.ศ. เป็น พ.ศ. สำหรับแสดงผล ---
def format_date_thai(dt):
    thai_year = dt.year + 543
    return f"{dt.day:02d}/{dt.month:02d}/{thai_year}"
    
# --- ฟังก์ชันช่วยคำนวณวันสิ้นเดือนของงวดที่ n ---
def get_end_of_month_by_index(start_date, month_index):
    target_year = start_date.year + (start_date.month - 1 + month_index) // 12
    target_month = (start_date.month - 1 + month_index) % 12 + 1
    first_of_target_month = date(target_year, target_month, 1)
    next_month_first = (first_of_target_month.replace(day=1) + timedelta(days=32)).replace(day=1)
    return next_month_first - timedelta(days=1)

# --- ฟังก์ชันหา "วันสิ้นสุดไตรมาส" ของไตรมาสถัดไปจากวันที่กำหนด ---
def get_next_quarter_end(current_date):
    y = current_date.year
    m = current_date.month
    if m <= 3:
        return date(y, 3, 31)
    elif m <= 6:
        return date(y, 6, 30)
    elif m <= 9:
        return date(y, 9, 30)
    else:
        return date(y, 12, 31)

# --- 1. ข้อมูลตั้งต้นปัจจุบัน ---
st.header("1. ข้อมูลหนี้ปัจจุบัน")
col1, col2, col3 = st.columns(3)
with col1:
    principal_current = st.number_input("ยอดเงินต้นคงเหลือปัจจุบัน (บาท)", value=100000.0, step=1000.0, format="%.2f")
with col2:
    annual_rate = st.number_input("ดอกเบี้ย (% ต่อปี)", value=6.575, step=0.750, format="%.3f")
with col3:
    as_of_date = st.date_input("ข้อมูล ณ วันที่", value=date.today())

accrued_interest_input = st.number_input("ดอกเบี้ยค้างจ่าย ณ ปัจจุบัน (บาท)", value=0.0, step=100.0, format="%.2f")

st.info(f"📌 **เงินต้นปัจจุบัน:** {principal_current:,.2f} บาท | **ดอกเบี้ยค้างจ่าย:** {accrued_interest_input:,.2f} บาท")

# --- 2. การคำนวณวางแผนอนาคต (ตัดรอบทุกสิ้นเดือน) ---
st.header("2. วางแผนอนาคต")
tab1, tab2, tab3, tab4 = st.tabs(["🔮 ยอดหนี้ในอนาคต", "⏳ ระยะเวลาหมดหนี้", "💵 ค่างวดที่ต้องส่ง", "⚖️ เปรียบเทียบ"])

with tab1:
    st.subheader("คำนวณยอดหนี้ตามวันที่ระบุ")
    
    # ค่าเริ่มต้นวันที่เป็นวันสิ้นสุดไตรมาสอัตโนมัติ (ข้อ 4)
    default_target_date = get_next_quarter_end(as_of_date)
    target_date = st.date_input("เลือกวันที่ต้องการเช็คยอดหนี้", value=default_target_date)
    
    if st.button("คำนวณยอดหนี้ ณ วันที่เลือก", key="btn1"):
        if target_date <= as_of_date:
            st.error("กรุณาเลือกวันที่อยู่ในอนาคต (มากกว่าวันที่ปัจจุบัน)")
        else:
            sim_balance = max(0, principal_current)
            days_diff = (target_date - as_of_date).days
            
            # ดอกเบี้ยสะสมตามระยะเวลาที่เลือก
            sim_interest_new = sim_balance * (annual_rate / 100.0) * (days_diff / 365.0)
            total_interest = accrued_interest_input + sim_interest_new
            est_total = sim_balance + total_interest

            # คำนวณดอกเบี้ย 1 วัน, 1 เดือน (30 วัน), และ 1 ปี
            interest_1_day = sim_balance * (annual_rate / 100.0) * (1.0 / 365.0)
            interest_1_month = sim_balance * (annual_rate / 100.0) * (30.0 / 365.0)
            interest_1_year = sim_balance * (annual_rate / 100.0)
            
            # คำนวณดอกเบี้ย 15 เดือนจากต้นเงินปัจจุบัน
            interest_450_days = sim_balance * (annual_rate / 100.0) * (450.0 / 365.0)
            
            # คำนวณสัดส่วน 30% และ 15% ของดอกเบี้ยสะสมทั้งหมด
            interest_30_pct = total_interest * 0.30
            interest_15_pct = total_interest * 0.15

            formatted_target_date = format_date_thai(target_date)
            st.info(f"📅 ณ วันที่ {formatted_target_date} (อีก {days_diff} วันข้างหน้า)")
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("เงินต้นคงเหลือ", f"{sim_balance:,.2f} บาท")
            col_b.metric("ดอกเบี้ยสะสมทั้งหมด", f"{total_interest:,.2f} บาท")
            col_c.metric("ยอดหนี้รวมทั้งสิ้น", f"{est_total:,.2f} บาท")

            st.write("---")
            st.subheader("💸 ดอกเบี้ย")
            col_d1, col_m1, col_y1 = st.columns(3)
            col_d1.metric("ดอกเบี้ย 1 วัน", f"{interest_1_day:,.2f} บาท")
            col_m1.metric("ดอกเบี้ย 1 เดือน (30 วัน)", f"{interest_1_month:,.2f} บาท")
            col_y1.metric("ดอกเบี้ย 1 ปี", f"{interest_1_year:,.2f} บาท")
            
            st.write("---")
            st.subheader("💡 ข้อมูลดอกเบี้ยเพิ่มเติม")
            
            col_x, col_y, col_z = st.columns(3)
            
            # เงื่อนไขข้อ 1: ถ้ายอดดอกเบี้ยสะสมมากกว่าดอกเบี้ย 450 วัน ให้แสดงเป็นสีแดง
            if total_interest > interest_450_days:
                col_x.markdown(f"**ดอกเบี้ย 15 เดือน:** <span style='color:red; font-size:30px; font-weight:bold;'>{interest_450_days:,.2f} บาท</span>", unsafe_allow_html=True)
            else:
                col_x.metric("ดอกเบี้ย 15 เดือน", f"{interest_450_days:,.2f} บาท")
                
            col_y.metric("30% ของดอกเบี้ยสะสม", f"{interest_30_pct:,.2f} บาท")
            col_z.metric("15% ของดอกเบี้ยสะสม", f"{interest_15_pct:,.2f} บาท")

with tab2:
    st.subheader("แผนผ่อนชำระด้วยยอดคงที่ต่อเดือน (ทุกสิ้นเดือน)")
    fixed_pmt = st.number_input("จำนวนเงินที่จะผ่อนต่อเดือน (บาท)", value=5000.0, step=500.0, format="%.2f", key="inp_pmt")
    
    if st.button("คำนวณระยะเวลาและแสดงตาราง", key="btn2"):
        bal_target = max(0, principal_current)
        
        if bal_target <= 0 and accrued_interest_input <= 0:
            st.success("คุณไม่มีหนี้คงเหลือแล้วครับ!")
        else:
            temp_balance = bal_target
            temp_accrued_interest = accrued_interest_input
            future_schedule = []
            month_count = 0
            prev_date = as_of_date
            
            while (temp_balance > 0 or temp_accrued_interest > 0) and month_count < 360:
                month_count += 1
                next_end_date = get_end_of_month_by_index(as_of_date, month_count)
                days_m = (next_end_date - prev_date).days
                
                # ดอกเบี้ยที่งอกขึ้นมาใหม่ในงวดนี้
                interest_new = temp_balance * (annual_rate / 100.0) * (days_m / 365.0)
                total_interest_due = temp_accrued_interest + interest_new
                
                if fixed_pmt > total_interest_due:
                    interest_paid = total_interest_due
                    principal_paid = fixed_pmt - total_interest_due
                    if principal_paid > temp_balance:
                        principal_paid = temp_balance
                    actual_pay = interest_paid + principal_paid
                    temp_accrued_interest = 0.0
                else:
                    interest_paid = fixed_pmt
                    principal_paid = 0.0
                    actual_pay = fixed_pmt
                    temp_accrued_interest = total_interest_due - fixed_pmt
                
                temp_balance -= principal_paid
                if temp_balance < 0: temp_balance = 0
                
                future_schedule.append({
                    "งวดที่": month_count,
                    "วันที่": format_date_thai(next_end_date),
                    "ยอดจ่าย": round(actual_pay, 2),
                    "ตัดดอกเบี้ย": round(interest_paid, 2),
                    "ดอกเบี้ยคงเหลือ": round(temp_accrued_interest, 2),
                    "ตัดเงินต้น": round(principal_paid, 2),
                    "เงินต้นคงเหลือ": round(temp_balance, 2)
                })
                
                prev_date = next_end_date
                if temp_balance == 0 and temp_accrued_interest == 0: break
            
            df_res = pd.DataFrame(future_schedule)
            
            total_row = pd.DataFrame({
                "งวดที่": ["รวมทั้งสิ้น"],
                "วันที่": [""],
                "ยอดจ่าย": [round(df_res["ยอดจ่าย"].sum(), 2)],
                "ตัดดอกเบี้ย": [round(df_res["ตัดดอกเบี้ย"].sum(), 2)],
                "ดอกเบี้ยคงเหลือ": [""],
                "ตัดเงินต้น": [round(df_res["ตัดเงินต้น"].sum(), 2)],
                "เงินต้นคงเหลือ": [""]
            })
            
            years = month_count // 12
            rem_m = month_count % 12
            if month_count >= 360 and (temp_balance > 0 or temp_accrued_interest > 0):
                st.warning("⚠️ ยอดผ่อนต่อเดือนน้อยเกินไป ทำให้ไม่สามารถปลดหนี้ได้หมดภายใน 30 ปี")
            else:
                st.warning(f"⏳ ต้องผ่อนประมาณ **{years} ปี {rem_m} เดือน** ถึงจะหมดหนี้")
            
            # --- 1. ตารางสำหรับแสดงบนหน้าเว็บ (ไม่มีข้อความหมายเหตุ) ---
            df_res_display = pd.concat([df_res, total_row], ignore_index=True)
            st.dataframe(df_res_display, use_container_width=True)
            
            # --- 2. ตารางสำหรับดาวน์โหลดไฟล์ CSV (เพิ่มข้อความหมายเหตุเฉพาะตอนเซฟ) ---
            disclaimer_row = pd.DataFrame({
                "งวดที่": ["เอกสารนี้จัดทำขึ้นเพื่อการจำลองแผนการชำระหนี้เท่านั้น ไม่ใช่สัญญาผูกพันทางกฎหมาย"],
                "วันที่": [""],
                "ยอดจ่าย": [""],
                "ตัดดอกเบี้ย": [""],
                "ดอกเบี้ยคงเหลือ": [""],
                "ตัดเงินต้น": [""],
                "เงินต้นคงเหลือ": [""]
            })
            df_res_display_with_note = pd.concat([df_res_display, disclaimer_row], ignore_index=True)
            
            csv_data = df_res_display_with_note.to_csv(index=False).encode('utf-8-sig')
            
            st.download_button(
                label="📥 ดาวน์โหลดแผนการชำระหนี้ (CSV)",
                data=csv_data,
                file_name="loan_payment_plan.csv",
                mime="text/csv",
                key="download_csv_btn_2"
            )

            # --- สัดส่วนยอดชำระทั้งหมด ---
            st.subheader("📊 สัดส่วนยอดชำระทั้งหมด (เงินต้นรวม vs ดอกเบี้ยรวม)")
            total_principal_paid = df_res["ตัดเงินต้น"].sum()
            total_interest_paid = df_res["ตัดดอกเบี้ย"].sum()
            grand_total = total_principal_paid + total_interest_paid
            
            if grand_total > 0:
                p_pct = (total_principal_paid / grand_total) * 100
                i_pct = (total_interest_paid / grand_total) * 100
                
                col_p1, col_p2 = st.columns(2)
                col_p1.metric("💰 สัดส่วนเงินต้นรวม", f"{p_pct:.2f}%", f"{total_principal_paid:,.2f} บาท")
                col_p2.metric("📈 สัดส่วนดอกเบี้ยรวม", f"{i_pct:.2f}%", f"{total_interest_paid:,.2f} บาท")

            # --- กราฟแสดงแนวโน้มยอดเงินต้นคงเหลือ (Tab 2) - โทนเขียวมีพื้นหลัง ---
            st.subheader("📈 กราฟแสดงแนวโน้มยอดเงินต้นคงเหลือ")
            
            fig = px.line(
                df_res, 
                x="งวดที่", 
                y="เงินต้นคงเหลือ", 
                labels={"งวดที่": "งวดที่", "เงินต้นคงเหลือ": "เงินต้นคงเหลือ (บาท)"},
                markers=True
            )
            
            # ปรับแต่งเส้น สีจุด และเพิ่มพื้นหลังใต้กราฟ (Fill)
            fig.update_traces(
                line=dict(color='#2ECC71', width=3),  # เส้นสีเขียว
                marker=dict(size=6, color='#27AE60'), # จุดสีเขียวเข้ม
                fill='tozeroy',                       # เติมพื้นที่ลงไปถึงแกน X ด้านล่าง
                fillcolor='rgba(46, 204, 113, 0.15)'  # สีเขียวโปร่งแสง (ความจาง 15%)
            )
            
            fig.update_layout(
                xaxis=dict(fixedrange=True),
                yaxis=dict(
                    fixedrange=True,
                    tickformat=","
                ),
                dragmode=False
            )
            
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False})

            # --- กราฟแสดงสัดส่วนเงินต้นและดอกเบี้ยที่จ่ายในแต่ละงวด (Tab 2) ---
            st.subheader("📊 สัดส่วนเงินต้นและดอกเบี้ยที่จ่ายในแต่ละงวด")
            fig_mix = px.bar(
                df_res, 
                x="งวดที่", 
                y=["ตัดเงินต้น", "ตัดดอกเบี้ย"],  # เอา 2 ค่ามารวมกันในกราฟเดียว
                labels={"value": "จำนวนเงิน (บาท)", "variable": "รายการ", "งวดที่": "งวดที่"},
                barmode="stack"  # ซ้อนแท่งกัน เพื่อให้เห็นยอดรวมค่างวดพอดี
            )
            
            # กำหนดสีให้สวยงาม: เงินต้น (สีเขียว), ดอกเบี้ย (สีส้ม/แดงอ่อน หรือสีเทา)
            fig_mix.update_traces(
                marker=dict(line=dict(width=0))
            )
            
            # ปรับแต่งธีมสีของแท่ง (ตัวอย่าง: เงินต้น = เขียว, ดอกเบี้ย = ส้มอมแดง)
            # หรือจะใช้สีโทนเขียวเข้ม/อ่อนคู่กันก็ได้ครับ
            colors = {'ตัดเงินต้น': '#2ECC71', 'ตัดดอกเบี้ย': '#E74C3C'}
            for i, data in enumerate(fig_mix.data):
                key_name = data.name
                if key_name in colors:
                    data.marker.color = colors[key_name]

            # ล็อกแกน ไม่ให้เลื่อน และจัดรูปแบบตัวเลข
            fig_mix.update_layout(
                xaxis=dict(fixedrange=True),
                yaxis=dict(
                    fixedrange=True,
                    tickformat=","
                ),
                dragmode=False,
                legend=dict(
                    title="",
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            st.plotly_chart(fig_mix, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False})

with tab3:
    st.subheader("คำนวณงวดต่อเดือนให้หมดหนี้ตามกำหนด (ทุกสิ้นเดือน)")
# เพิ่มตัวเลือกหน่วย: ระบุเป็นเดือน / ระบุเป็นปี / หรือเลือกวันที่ต้องการปิดยอดเอง
    calc_unit = st.radio("เลือกรูปแบบการกำหนดระยะเวลา", ["ระบุเป็นเดือน", "ระบุเป็นปี", "ระบุวันที่ต้องการปิดยอดเอง"], horizontal=True, key="calc_unit_radio")
    
    if calc_unit == "ระบุเป็นปี":
        col_y1, col_y2 = st.columns(2)
        with col_y1:
            target_years_input = st.number_input("จำนวนปี", value=1.0, min_value=0.0, step=1.0, format="%.1f", key="inp_years")
        with col_y2:
            target_months = int(target_years_input * 12)
            st.markdown(f"<div style='margin-top: 28px;'><b>คิดเป็น:</b> {target_months} เดือน</div>", unsafe_allow_html=True)
            
    elif calc_unit == "ระบุวันที่ต้องการปิดยอดเอง":
        # กำหนดค่าเริ่มต้นให้ไปข้างหน้า 1 ปี หรือเลือกตามต้องการ
        custom_target_date = st.date_input("เลือกวันที่ต้องการปิดยอดหนี้", value=as_of_date + timedelta(days=365), key="inp_custom_date")
        
        # คำนวณหาจำนวนเดือนระหว่างวันปัจจุบันถึงวันที่เลือก (คิดคร่าวๆ จากส่วนต่างเดือน)
        if custom_target_date <= as_of_date:
            st.error("กรุณาเลือกวันที่อยู่ในอนาคต (มากกว่าวันที่ปัจจุบัน)")
            target_months = 0
        else:
            # คำนวณจำนวนเดือนห่างกัน
            diff_months = (custom_target_date.year - as_of_date.year) * 12 + (custom_target_date.month - as_of_date.month)
            # ถ้าวันสิ้นเดือนยังไม่ถึง ให้ปรับจำนวนเดือนให้เหมาะสม
            if custom_target_date.day < as_of_date.day and diff_months > 0:
                diff_months -= 1
            target_months = max(1, diff_months)
            
            thai_target_date_str = format_date_thai(custom_target_date)
            st.markdown(f"📌 **เป้าหมายปิดยอดวันที่:** {thai_target_date_str} (ประมาณ **{target_months} เดือน**) <small style='color: gray;'>(ระบบจะคำนวณตัดรอบทุกสิ้นเดือน)</small>", unsafe_allow_html=True)
    else:
        target_months = st.number_input("ระยะเวลาที่ต้องการ (เดือน)", value=12, min_value=1, step=1, key="inp_months")
    
    if st.button("คำนวณค่างวดและแสดงตาราง", key="btn3"):
        monthly_rate = (annual_rate / 100) / 12
        bal_target = max(0, principal_current)
        
        if bal_target <= 0 and accrued_interest_input <= 0:
            st.success("คุณไม่มีหนี้คงเหลือแล้วครับ!")
        elif target_months <= 0:
            st.error("กรุณากำหนดระยะเวลาหรือวันที่ให้ถูกต้องมากกว่า 0 เดือน")
        else:
            total_debt_approx = bal_target + accrued_interest_input
            if monthly_rate > 0:
                pmt_calc = npf.pmt(monthly_rate, target_months, -total_debt_approx)
            else:
                pmt_calc = total_debt_approx / target_months
            st.success(f"💵 ต้องส่งงวดละประมาณ **{pmt_calc:,.2f} บาท** ทุกสิ้นเดือน เป็นเวลา {target_months} เดือน")
            
            temp_balance = bal_target
            temp_accrued_interest = accrued_interest_input
            future_schedule_2 = []
            prev_date = as_of_date
            
            for m in range(1, int(target_months) + 1):
                if temp_balance <= 0 and temp_accrued_interest <= 0: break
                next_end_date = get_end_of_month_by_index(as_of_date, m)
                days_m = (next_end_date - prev_date).days
                
                interest_new = temp_balance * (annual_rate / 100.0) * (days_m / 365.0)
                total_interest_due = temp_accrued_interest + interest_new
                
                # หากเป็นงวดสุดท้าย บังคับตัดเงินต้นส่วนที่เหลือทั้งหมดเพื่อให้ยอดปิดจบพอดี
                if m == target_months or temp_balance + total_interest_due <= pmt_calc:
                    interest_paid = total_interest_due
                    principal_paid = temp_balance
                    actual_pay = interest_paid + principal_paid
                    temp_accrued_interest = 0.0
                else:
                    interest_paid = total_interest_due
                    principal_paid = pmt_calc - interest_paid
                    if principal_paid < 0:
                        interest_paid = pmt_calc
                        principal_paid = 0.0
                        actual_pay = pmt_calc
                        temp_accrued_interest = total_interest_due - pmt_calc
                    else:
                        actual_pay = pmt_calc
                        temp_accrued_interest = 0.0
                
                temp_balance -= principal_paid
                if temp_balance < 0: temp_balance = 0
                
                future_schedule_2.append({
                    "งวดที่": m,
                    "วันที่": format_date_thai(next_end_date),
                    "ยอดจ่าย": round(actual_pay, 2),
                    "ตัดดอกเบี้ย": round(interest_paid, 2),
                    "ดอกเบี้ยคงเหลือ": round(temp_accrued_interest, 2),
                    "ตัดเงินต้น": round(principal_paid, 2),
                    "เงินต้นคงเหลือ": round(temp_balance, 2)
                })
                prev_date = next_end_date
                
            df_res2 = pd.DataFrame(future_schedule_2)
            
            total_row2 = pd.DataFrame({
                "งวดที่": ["รวมทั้งสิ้น"],
                "วันที่": [""],
                "ยอดจ่าย": [round(df_res2["ยอดจ่าย"].sum(), 2)],
                "ตัดดอกเบี้ย": [round(df_res2["ตัดดอกเบี้ย"].sum(), 2)],
                "ดอกเบี้ยคงเหลือ": [""],
                "ตัดเงินต้น": [round(df_res2["ตัดเงินต้น"].sum(), 2)],
                "เงินต้นคงเหลือ": [""]
            })
            df_res2_display = pd.concat([df_res2, total_row2], ignore_index=True)
            
            # --- 1. แสดงตารางปกติบนหน้าเว็บ (ไม่มีข้อความหมายเหตุ) ---
            st.dataframe(df_res2_display, use_container_width=True)
            
            # --- 2. เตรียมตารางสำหรับดาวน์โหลดไฟล์ CSV (เพิ่มข้อความหมายเหตุเฉพาะตอนเซฟ) ---
            disclaimer_row2 = pd.DataFrame({
                "งวดที่": ["เอกสารนี้จัดทำขึ้นเพื่อการจำลองแผนการชำระหนี้เท่านั้น ไม่ใช่สัญญาผูกพันทางกฎหมาย"],
                "วันที่": [""],
                "ยอดจ่าย": [""],
                "ตัดดอกเบี้ย": [""],
                "ดอกเบี้ยคงเหลือ": [""],
                "ตัดเงินต้น": [""],
                "เงินต้นคงเหลือ": [""]
            })
            df_res2_display_with_note = pd.concat([df_res2_display, disclaimer_row2], ignore_index=True)
            
            csv_data2 = df_res2_display_with_note.to_csv(index=False).encode('utf-8-sig')
            
            st.download_button(
                label="📥 ดาวน์โหลดตารางแผนการผ่อนชำระ (CSV)",
                data=csv_data2,
                file_name="loan_payment_plan_target.csv",
                mime="text/csv",
                key="download_csv_btn_3"  # ใช้ Key แยกไม่ให้ชนกับ Tab อื่น
            )


            # --- สัดส่วนยอดชำระทั้งหมด (แท็บที่ 3) ---
            st.subheader("📊 สัดส่วนยอดชำระทั้งหมด (เงินต้นรวม vs ดอกเบี้ยรวม)")
            total_principal_paid2 = df_res2["ตัดเงินต้น"].sum()
            total_interest_paid2 = df_res2["ตัดดอกเบี้ย"].sum()
            grand_total2 = total_principal_paid2 + total_interest_paid2
            
            if grand_total2 > 0:
                p_pct2 = (total_principal_paid2 / grand_total2) * 100
                i_pct2 = (total_interest_paid2 / grand_total2) * 100
                
                col_p3, col_p4 = st.columns(2)
                col_p3.metric("💰 สัดส่วนเงินต้นรวม", f"{p_pct2:.2f}%", f"{total_principal_paid2:,.2f} บาท")
                col_p4.metric("📈 สัดส่วนดอกเบี้ยรวม", f"{i_pct2:.2f}%", f"{total_interest_paid2:,.2f} บาท")
            
            # --- กราฟแสดงแนวโน้มยอดเงินต้นคงเหลือ (Tab 3) - โทนเขียวมีพื้นหลัง ---
            st.subheader("📈 กราฟแสดงแนวโน้มยอดเงินต้นคงเหลือ")
            
            fig2 = px.line(
                df_res2, 
                x="งวดที่", 
                y="เงินต้นคงเหลือ", 
                labels={"งวดที่": "งวดที่", "เงินต้นคงเหลือ": "เงินต้นคงเหลือ (บาท)"},
                markers=True
            )
            
            # ปรับแต่งเส้น สีจุด และเพิ่มพื้นหลังใต้กราฟ (Fill) สำหรับ Tab 3
            fig2.update_traces(
                line=dict(color='#2ECC71', width=3),  # เส้นสีเขียว
                marker=dict(size=6, color='#27AE60'), # จุดสีเขียวเข้ม
                fill='tozeroy',                       # เติมพื้นที่ลงไปถึงแกน X ด้านล่าง
                fillcolor='rgba(46, 204, 113, 0.15)'  # สีเขียวโปร่งแสง (ความจาง 15%)
            )
            
            fig2.update_layout(
                xaxis=dict(fixedrange=True),
                yaxis=dict(
                    fixedrange=True,
                    tickformat=","
                ),
                dragmode=False
            )
            
            st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False})
            
            # --- กราฟแสดงสัดส่วนเงินต้นและดอกเบี้ยที่จ่ายในแต่ละงวด (Tab 3) ---
            st.subheader("📊 สัดส่วนเงินต้นและดอกเบี้ยที่จ่ายในแต่ละงวด")   
            fig_mix2 = px.bar(
                df_res2, 
                x="งวดที่", 
                y=["ตัดเงินต้น", "ตัดดอกเบี้ย"],  # เอา 2 ค่ามารวมกันในกราฟเดียว
                labels={"value": "จำนวนเงิน (บาท)", "variable": "รายการ", "งวดที่": "งวดที่"},
                barmode="stack"  # ซ้อนแท่งกัน เพื่อให้เห็นยอดรวมค่างวดพอดี
            )
            
            # กำหนดสีให้สวยงาม: เงินต้น (สีเขียว), ดอกเบี้ย (สีส้ม/แดงอ่อน หรือสีเทา)
            fig_mix2.update_traces(
                marker=dict(line=dict(width=0))
            )
            
            # ปรับแต่งธีมสีของแท่ง (ตัวอย่าง: เงินต้น = เขียว, ดอกเบี้ย = ส้มอมแดง)
            # หรือจะใช้สีโทนเขียวเข้ม/อ่อนคู่กันก็ได้ครับ
            colors = {'ตัดเงินต้น': '#2ECC71', 'ตัดดอกเบี้ย': '#E74C3C'}
            for i, data in enumerate(fig_mix2.data):
                key_name = data.name
                if key_name in colors:
                    data.marker.color = colors[key_name]

            # ล็อกแกน ไม่ให้เลื่อน และจัดรูปแบบตัวเลข
            fig_mix2.update_layout(
                xaxis=dict(fixedrange=True),
                yaxis=dict(
                    fixedrange=True,
                    tickformat=","
                ),
                dragmode=False,
                legend=dict(
                    title="",
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            st.plotly_chart(fig_mix2, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False})

with tab4:
    st.subheader("⚖️ เปรียบเทียบ")
    st.markdown("🤜ร่างกายต้องการปะทะ🤛")

    # --- ส่วนเลือกรูปแบบการคำนวณ ---
    compare_mode = st.radio(
        "เลือกวิธีเปรียบเทียบ",
        [
            "เปรียบเทียบด้วย 'ยอดผ่อนต่อเดือน'", 
            "เปรียบเทียบด้วย 'ระยะเวลาผ่อน'"
        ],
        key="compare_mode_radio"
    )
    
    col_input_a, col_input_b = st.columns(2)
    
    if "ยอดผ่อนต่อเดือน" in compare_mode:
        with col_input_a:
            st.markdown("### 📌 แผนที่ 1")
            plan_a_val = st.number_input("ค่างวดต่อเดือน แผน 1 (บาท)", value=5000.0, step=500.0, key="p1_pmt_mode1")
        with col_input_b:
            st.markdown("### 📌 แผนที่ 2")
            plan_b_val = st.number_input("ค่างวดต่อเดือน แผน 2 (บาท)", value=8000.0, step=500.0, key="p2_pmt_mode1")
    else:
        with col_input_a:
            st.markdown("### 📌 แผนที่ 1")
            plan_a_val = st.number_input("ระยะเวลาเป้าหมาย แผน 1 (เดือน)", value=12, min_value=1, step=1, key="p1_m_mode2")
        with col_input_b:
            st.markdown("### 📌 แผนที่ 2")
            plan_b_val = st.number_input("ระยะเวลาเป้าหมาย แผน 2 (เดือน)", value=6, min_value=1, step=1, key="p2_m_mode2")

    if st.button("🚀 คำนวณและเปรียบเทียบแบบละเอียด", key="btn_compare_full"):
        bal_target = max(0, principal_current)
        
        if bal_target <= 0 and accrued_interest_input <= 0:
            st.success("คุณไม่มีหนี้คงเหลือแล้วครับ!")
        else:
            def simulate_until_debt_free_with_schedule(mode, val):
                temp_bal = bal_target
                temp_acc_int = accrued_interest_input
                prev_dt = as_of_date
                total_int_paid = 0.0
                schedule = []
                
                monthly_rate = (annual_rate / 100.0) / 12.0
                total_debt_approx = temp_bal + temp_acc_int
                
                if "ระยะเวลา" in mode:
                    target_m = int(val)
                    if monthly_rate > 0:
                        calc_pmt = npf.pmt(monthly_rate, target_m, -total_debt_approx)
                    else:
                        calc_pmt = total_debt_approx / target_m
                else:
                    calc_pmt = float(val)
                
                approx_first_interest = temp_bal * (annual_rate / 100.0) * (30 / 365.0) + temp_acc_int
                if "ยอดผ่อนต่อเดือน" in mode and calc_pmt <= approx_first_interest:
                    return None, None, None, calc_pmt, pd.DataFrame(), "NEVER_END"

                m = 1
                while temp_bal > 0 or temp_acc_int > 0:
                    if m > 1200: #เกิน 100 ปี ถือว่าหนี้ไม่มีวันหมดเช่นกัน
                        return None, None, None, calc_pmt, pd.DataFrame(), "NEVER_END"
                        
                    next_end_dt = get_end_of_month_by_index(as_of_date, m)
                    days_m = (next_end_dt - prev_dt).days
                    
                    interest_new = temp_bal * (annual_rate / 100.0) * (days_m / 365.0)
                    total_interest_due = temp_acc_int + interest_new
                    
                    if calc_pmt <= total_interest_due and temp_bal > 0:
                        return None, None, None, calc_pmt, pd.DataFrame(), "NEVER_END"

                    is_last_target_month = ("ระยะเวลา" in mode and m == int(val))
                    
                    if is_last_target_month or (temp_bal + total_interest_due <= calc_pmt):
                        interest_paid = total_interest_due
                        principal_paid = temp_bal
                        actual_pay = interest_paid + principal_paid
                        temp_acc_int = 0.0
                    else:
                        interest_paid = total_interest_due
                        principal_paid = calc_pmt - interest_paid
                        if principal_paid < 0:
                            interest_paid = calc_pmt
                            principal_paid = 0.0
                            actual_pay = calc_pmt
                            temp_acc_int = total_interest_due - calc_pmt
                        else:
                            actual_pay = calc_pmt
                            temp_acc_int = 0.0
                    
                    total_int_paid += interest_paid
                    temp_bal -= principal_paid
                    if temp_bal < 0: temp_bal = 0
                    
                    schedule.append({
                        "งวดที่": m,
                        "ยอดที่จ่าย": round(actual_pay, 2),
                        "ดอกเบี้ย": round(interest_paid, 2),
                        "ตัดต้น": round(principal_paid, 2),
                        "เงินต้นคงเหลือ": round(temp_bal, 2)
                    })
                    
                    if temp_bal <= 0 and temp_acc_int <= 0:
                        break
                        
                    prev_dt = next_end_dt
                    m += 1
                    
                total_months_used = len(schedule)
                total_paid_all = sum([s["ยอดที่จ่าย"] for s in schedule])
                first_month_pmt = schedule[0]["ยอดที่จ่าย"] if schedule else calc_pmt
                return total_months_used, total_int_paid, total_paid_all, first_month_pmt, pd.DataFrame(schedule), "OK"

            res_a = simulate_until_debt_free_with_schedule(compare_mode, plan_a_val)
            res_b = simulate_until_debt_free_with_schedule(compare_mode, plan_b_val)
            
            m_a, int_a, paid_a, pmt_a, df_a, status_a = res_a
            m_b, int_b, paid_b, pmt_b, df_b, status_b = res_b
            
            st.markdown("---")
            st.subheader("📊 ผลลัพธ์การเปรียบเทียบ")
            
            if status_a == "NEVER_END" or status_b == "NEVER_END":
                col_err1, col_err2 = st.columns(2)
                with col_err1:
                    st.markdown("### 📌 แผนที่ 1")
                    if status_a == "NEVER_END":
                        st.error("🚨 **ข้อสรุป:** ผ่อนน้อยกว่าดอกเบี้ย ขออภัยครับ **ชาตินี้หนี้ไม่มีวันหมด** ครับ!")
                    else:
                        st.metric("💵 ค่างวดที่ต้องจ่าย", f"{pmt_a:,.2f} บาท/เดือน", delta_color="off")
                        st.metric("⏳ ระยะเวลาปลดหนี้", f"{m_a} เดือน")
                with col_err2:
                    st.markdown("### 📌 แผนที่ 2")
                    if status_b == "NEVER_END":
                        st.error("🚨 **ข้อสรุป:** ผ่อนน้อยกว่าดอกเบี้ย ขออภัยครับ **ชาตินี้หนี้ไม่มีวันหมด** ครับ!")
                    else:
                        st.metric("💵 ค่างวดที่ต้องจ่าย", f"{pmt_b:,.2f} บาท/เดือน", delta_color="off")
                        st.metric("⏳ ระยะเวลาปลดหนี้", f"{m_b} เดือน")
            else:
                col_res1, col_res2 = st.columns(2)
                
                diff_pmt_a = pmt_a - pmt_b       
                diff_m_a = m_a - m_b             
                diff_i_a = int_a - int_b         
                diff_paid_a = paid_a - paid_b    
                
                diff_pmt_b = pmt_b - pmt_a       
                diff_m_b = m_b - m_a             
                diff_i_b = int_b - int_a         
                diff_paid_b = paid_b - paid_a    
                
                def format_months_plain(total_months):
                    if total_months > 12:
                        y = total_months // 12
                        m = total_months % 12
                        return f"{total_months} เดือน ({y} ปี {m} เดือน)"
                    return f"{total_months} เดือน"

                with col_res1:
                    st.markdown("### 📌 แผนที่ 1")
                    st.metric("💵 ค่างวดที่ต้องจ่าย", f"{pmt_a:,.2f} บาท/เดือน", f"ต่างกัน {abs(diff_pmt_a):,.2f} บาท" if diff_pmt_a != 0 else "เท่ากัน", delta_color="off")
                    st.metric("⏳ ระยะเวลาปลดหนี้", format_months_plain(m_a), f"เร็วกว่า {abs(diff_m_a)} เดือน" if diff_m_a < 0 else (f"ช้ากว่า {diff_m_a} เดือน" if diff_m_a > 0 else "เท่ากัน"), delta_color="normal" if diff_m_a < 0 else ("inverse" if diff_m_a > 0 else "off"))
                    st.metric("💸 ดอกเบี้ยรวมทั้งหมด", f"{int_a:,.2f} บาท", f"ประหยัด {abs(diff_i_a):,.2f} บาท" if diff_i_a < 0 else (f"จ่ายเพิ่ม {diff_i_a:,.2f} บาท" if diff_i_a > 0 else "เท่ากัน"), delta_color="normal" if diff_i_a < 0 else ("inverse" if diff_i_a > 0 else "off"))
                    st.metric("💰 ยอดจ่ายรวมทั้งสิ้น", f"{paid_a:,.2f} บาท", f"น้อยกว่า {abs(diff_paid_a):,.2f} บาท" if diff_paid_a < 0 else (f"มากกว่า {diff_paid_a:,.2f} บาท" if diff_paid_a > 0 else "เท่ากัน"), delta_color="normal" if diff_paid_a < 0 else ("inverse" if diff_paid_a > 0 else "off"))
                    
                with col_res2:
                    st.markdown("### 📌 แผนที่ 2")
                    st.metric("💵 ค่างวดที่ต้องจ่าย", f"{pmt_b:,.2f} บาท/เดือน", f"ต่างกัน {abs(diff_pmt_b):,.2f} บาท" if diff_pmt_b != 0 else "เท่ากัน", delta_color="off")
                    st.metric("⏳ ระยะเวลาปลดหนี้", format_months_plain(m_b), f"เร็วกว่า {abs(diff_m_b)} เดือน" if diff_m_b < 0 else (f"ช้ากว่า {diff_m_b} เดือน" if diff_m_b > 0 else "เท่ากัน"), delta_color="normal" if diff_m_b < 0 else ("inverse" if diff_m_b > 0 else "off"))
                    st.metric("💸 ดอกเบี้ยรวมทั้งหมด", f"{int_b:,.2f} บาท", f"ประหยัด {abs(diff_i_b):,.2f} บาท" if diff_i_b < 0 else (f"จ่ายเพิ่ม {diff_i_b:,.2f} บาท" if diff_i_b > 0 else "เท่ากัน"), delta_color="normal" if diff_i_b < 0 else ("inverse" if diff_i_b > 0 else "off"))
                    st.metric("💰 ยอดจ่ายรวมทั้งสิ้น", f"{paid_b:,.2f} บาท", f"น้อยกว่า {abs(diff_paid_b):,.2f} บาท" if diff_paid_b < 0 else (f"มากกว่า {diff_paid_b:,.2f} บาท" if diff_paid_b > 0 else "เท่ากัน"), delta_color="normal" if diff_paid_b < 0 else ("inverse" if diff_paid_b > 0 else "off"))
                    
                st.markdown("---")
                if int_b < int_a:
                    saving_amt = int_a - int_b
                    saving_months = m_a - m_b
                    st.success(f"🤠 **สรุป:** หากเลือก **แผนที่ 2** คุณจะ **หมดหนี้เร็วขึ้น {saving_months} เดือน** และ **ประหยัดดอกเบี้ยไปได้ถึง {saving_amt:,.2f} บาท** เมื่อเทียบกับแผนที่ 1!")
                elif int_a < int_b:
                    saving_amt = int_b - int_a
                    saving_months = m_b - m_a
                    st.success(f"🤠 **สรุป:** หากเลือก **แผนที่ 1** คุณจะ **หมดหนี้เร็วขึ้น {saving_months} เดือน** และ **ประหยัดดอกเบี้ยไปได้ถึง {saving_amt:,.2f} บาท** เมื่อเทียบกับแผนที่ 2!")
                else:
                    st.info("ℹ️ ทั้งสองแผนใช้ระยะเวลาและมีต้นทุนดอกเบี้ยรวมเท่ากันทุกประการครับ")

                st.markdown("---")
                st.subheader("📈 กราฟแนวโน้มยอดเงินต้น")
                
                df_a["แผน"] = "แผนที่ 1"
                df_b["แผน"] = "แผนที่ 2"
                df_compare = pd.concat([df_a, df_b], ignore_index=True)
                
                fig_comp_line = px.line(
                    df_compare, 
                    x="งวดที่", 
                    y="เงินต้นคงเหลือ", 
                    color="แผน",
                    markers=True,
                    labels={"งวดที่": "งวดที่", "เงินต้นคงเหลือ": "เงินต้นคงเหลือ (บาท)", "แผน": "แผนการชำระ"},
                    color_discrete_map={"แผนที่ 1": "#3498DB", "แผนที่ 2": "#2ECC71"}
                )
                fig_comp_line.update_layout(
                    xaxis=dict(fixedrange=True),
                    yaxis=dict(fixedrange=True, tickformat=","),
                    dragmode=False,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_comp_line, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False})
                
                st.subheader("📊 เปรียบเทียบเงินที่จ่าย")
                summary_bar_data = pd.DataFrame([
                    {"แผน": "แผนที่ 1", "ประเภท": "ดอกเบี้ยรวม", "จำนวนเงิน": round(int_a, 2)},
                    {"แผน": "แผนที่ 1", "ประเภท": "ยอดจ่ายรวมทั้งสิ้น", "จำนวนเงิน": round(paid_a, 2)},
                    {"แผน": "แผนที่ 2", "ประเภท": "ดอกเบี้ยรวม", "จำนวนเงิน": round(int_b, 2)},
                    {"แผน": "แผนที่ 2", "ประเภท": "ยอดจ่ายรวมทั้งสิ้น", "จำนวนเงิน": round(paid_b, 2)},
                ])
                
                fig_comp_bar = px.bar(
                    summary_bar_data,
                    x="แผน",
                    y="จำนวนเงิน",
                    color="ประเภท",
                    barmode="group",
                    text="จำนวนเงิน",
                    labels={"จำนวนเงิน": "จำนวนเงิน (บาท)", "แผน": "แผนการชำระ"},
                    color_discrete_map={"ดอกเบี้ยรวม": "#E74C3C", "ยอดจ่ายรวมทั้งสิ้น": "#34495E"}
                )
                fig_comp_bar.update_traces(texttemplate='%{text:,.2f}', textposition='outside')
                fig_comp_bar.update_layout(
                    xaxis=dict(fixedrange=True),
                    yaxis=dict(fixedrange=True, tickformat=","),
                    dragmode=False,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_comp_bar, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False})
