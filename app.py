import pandas as pd
import numpy_financial as npf
import streamlit as st
from datetime import date, timedelta

st.set_page_config(page_title="วางแผนชำระหนี้สินเชื่อ", page_icon="💰", layout="centered")

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

st.write("---")
accrued_interest_input = st.number_input("ดอกเบี้ยค้างจ่าย ณ ปัจจุบัน (บาท)", value=0.0, step=100.0, format="%.2f")

st.info(f"📌 **เงินต้นปัจจุบัน:** {principal_current:,.2f} บาท | **ดอกเบี้ยค้างจ่าย:** {accrued_interest_input:,.2f} บาท")

# --- 2. การคำนวณวางแผนอนาคต (ตัดรอบทุกสิ้นเดือน) ---
st.header("2. วางแผนอนาคต")
tab1, tab2, tab3 = st.tabs(["🔮 หนี้คงเหลือในอนาคต", "⏳ ระยะเวลาหมดหนี้", "💵 ค่างวดที่ต้องส่ง"])

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
            st.subheader("⏱️ ดอกเบี้ย (จากเงินต้นคงเหลือ)")
            col_d1, col_m1, col_y1 = st.columns(3)
            col_d1.metric("ดอกเบี้ย 1 วัน", f"{interest_1_day:,.2f} บาท")
            col_m1.metric("ดอกเบี้ย 1 เดือน (30 วัน)", f"{interest_1_month:,.2f} บาท")
            col_y1.metric("ดอกเบี้ย 1 ปี", f"{interest_1_year:,.2f} บาท")
            
            st.write("---")
            st.subheader("📌 ข้อมูลวิเคราะห์ดอกเบี้ยเพิ่มเติม")
            
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
                    "วันที่สิ้นเดือน": format_date_thai(next_end_date),
                    "ยอดที่ต้องจ่าย": round(actual_pay, 2),
                    "ดอกเบี้ยที่จ่าย": round(interest_paid, 2),
                    "ดอกเบี้ยค้างเหลือ": round(temp_accrued_interest, 2),
                    "ตัดเงินต้น": round(principal_paid, 2),
                    "เงินต้นคงเหลือ": round(temp_balance, 2)
                })
                
                prev_date = next_end_date
                if temp_balance == 0 and temp_accrued_interest == 0: break
            
            df_res = pd.DataFrame(future_schedule)
            
            total_row = pd.DataFrame({
                "งวดที่": ["รวมทั้งสิ้น"],
                "วันที่สิ้นเดือน": [""],
                "ยอดที่ต้องจ่าย": [round(df_res["ยอดที่ต้องจ่าย"].sum(), 2)],
                "ดอกเบี้ยที่จ่าย": [round(df_res["ดอกเบี้ยที่จ่าย"].sum(), 2)],
                "ดอกเบี้ยค้างเหลือ": [""],
                "ตัดเงินต้น": [round(df_res["ตัดเงินต้น"].sum(), 2)],
                "เงินต้นคงเหลือ": [""]
            })
            df_res_display = pd.concat([df_res, total_row], ignore_index=True)
            
            years = month_count // 12
            rem_m = month_count % 12
            if month_count >= 360 and (temp_balance > 0 or temp_accrued_interest > 0):
                st.warning("⚠️ ยอดผ่อนต่อเดือนน้อยเกินไป ทำให้ไม่สามารถปลดหนี้ได้หมดภายใน 30 ปี")
            else:
                st.warning(f"⏳ จะต้องผ่อนประมาณ **{years} ปี {rem_m} เดือน** ถึงจะหมดหนี้")
            
            st.dataframe(df_res_display, use_container_width=True)
            
            # --- สัดส่วนยอดชำระทั้งหมด ---
            st.subheader("📊 สัดส่วนยอดชำระทั้งหมด (เงินต้นรวม vs ดอกเบี้ยรวม)")
            total_principal_paid = df_res["ตัดเงินต้น"].sum()
            total_interest_paid = df_res["ดอกเบี้ยที่จ่าย"].sum()
            grand_total = total_principal_paid + total_interest_paid
            
            if grand_total > 0:
                p_pct = (total_principal_paid / grand_total) * 100
                i_pct = (total_interest_paid / grand_total) * 100
                
                col_p1, col_p2 = st.columns(2)
                col_p1.metric("💰 สัดส่วนเงินต้นรวม", f"{p_pct:.2f}%", f"{total_principal_paid:,.2f} บาท")
                col_p2.metric("📈 สัดส่วนดอกเบี้ยรวม", f"{i_pct:.2f}%", f"{total_interest_paid:,.2f} บาท")

with tab3:
    st.subheader("คำนวณงวดต่อเดือนให้หมดหนี้ตามกำหนด (ทุกสิ้นเดือน)")
# เพิ่มตัวเลือกหน่วย: ระบุเป็นเดือน / ระบุเป็นปี / หรือเลือกวันที่ต้องการปิดยอดเอง
    calc_unit = st.radio("เลือกรูปแบบการกำหนดระยะเวลา", ["ระบุเป็นเดือน", "ระบุเป็นปี", "ระบุวันที่ต้องการปิดยอดเอง"], horizontal=True, key="calc_unit_radio")
    
    if calc_unit == "ระบุเป็นปี":
        col_y1, col_y2 = st.columns(2)
        with col_y1:
            target_years_input = st.number_input("จำนวนปี", value=1, min_value=0.0, step=1.0, format="%.1f", key="inp_years")
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
                    "วันที่สิ้นเดือน": format_date_thai(next_end_date),
                    "ยอดที่ต้องจ่าย": round(actual_pay, 2),
                    "ดอกเบี้ยที่จ่าย": round(interest_paid, 2),
                    "ดอกเบี้ยค้างเหลือ": round(temp_accrued_interest, 2),
                    "ตัดเงินต้น": round(principal_paid, 2),
                    "เงินต้นคงเหลือ": round(temp_balance, 2)
                })
                prev_date = next_end_date
                
            df_res2 = pd.DataFrame(future_schedule_2)
            
            total_row2 = pd.DataFrame({
                "งวดที่": ["รวมทั้งสิ้น"],
                "วันที่สิ้นเดือน": [""],
                "ยอดที่ต้องจ่าย": [round(df_res2["ยอดที่ต้องจ่าย"].sum(), 2)],
                "ดอกเบี้ยที่จ่าย": [round(df_res2["ดอกเบี้ยที่จ่าย"].sum(), 2)],
                "ดอกเบี้ยค้างเหลือ": [""],
                "ตัดเงินต้น": [round(df_res2["ตัดเงินต้น"].sum(), 2)],
                "เงินต้นคงเหลือ": [""]
            })
            df_res2_display = pd.concat([df_res2, total_row2], ignore_index=True)
            
            st.dataframe(df_res2_display, use_container_width=True)
            
            # --- สัดส่วนยอดชำระทั้งหมด (แท็บที่ 3) ---
            st.subheader("📊 สัดส่วนยอดชำระทั้งหมด (เงินต้นรวม vs ดอกเบี้ยรวม)")
            total_principal_paid2 = df_res2["ตัดเงินต้น"].sum()
            total_interest_paid2 = df_res2["ดอกเบี้ยที่จ่าย"].sum()
            grand_total2 = total_principal_paid2 + total_interest_paid2
            
            if grand_total2 > 0:
                p_pct2 = (total_principal_paid2 / grand_total2) * 100
                i_pct2 = (total_interest_paid2 / grand_total2) * 100
                
                col_p3, col_p4 = st.columns(2)
                col_p3.metric("💰 สัดส่วนเงินต้นรวม", f"{p_pct2:.2f}%", f"{total_principal_paid2:,.2f} บาท")
                col_p4.metric("📈 สัดส่วนดอกเบี้ยรวม", f"{i_pct2:.2f}%", f"{total_interest_paid2:,.2f} บาท")
                
            
