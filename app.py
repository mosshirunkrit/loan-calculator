import pandas as pd
import numpy_financial as npf
import streamlit as st
from datetime import date, timedelta

st.set_page_config(page_title="วางแผนชำระหนี้สินเชื่อ", page_icon="💰", layout="centered")

st.markdown('<h2 style="font-size: 20px; font-weight: bold;">💰 วางแผนผ่อนชำระสินเชื่อ ทุ่งหว้า🔥</h2>', unsafe_allow_html=True)
st.write("เครื่องมือคำนวณและวางแผนชำระหนี้รายเดือน")

# --- ฟังก์ชันช่วยคำนวณวันสิ้นเดือนของงวดที่ n ---
def get_end_of_month_by_index(start_date, month_index):
    target_year = start_date.year + (start_date.month - 1 + month_index) // 12
    target_month = (start_date.month - 1 + month_index) % 12 + 1
    first_of_target_month = date(target_year, target_month, 1)
    next_month_first = (first_of_target_month.replace(day=1) + timedelta(days=32)).replace(day=1)
    return next_month_first - timedelta(days=1)

# --- 1. ข้อมูลตั้งต้นปัจจุบัน ---
st.header("1. ข้อมูลหนี้ปัจจุบัน")
col1, col2, col3 = st.columns(3)
with col1:
    principal_current = st.number_input("ยอดเงินต้นคงเหลือปัจจุบัน (บาท)", value=100000.0, step=1000.0, format="%.2f")
with col2:
    annual_rate = st.number_input("ดอกเบี้ย (% ต่อปี)", value=6.575, step=0.500, format="%.3f")
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
    target_date = st.date_input("เลือกวันที่ต้องการเช็คยอดหนี้", value=as_of_date + timedelta(days=90))
    
    if st.button("คำนวณยอดหนี้ ณ วันที่เลือก", key="btn1"):
        if target_date <= as_of_date:
            st.error("กรุณาเลือกวันที่อยู่ในอนาคต (มากกว่าวันที่ปัจจุบัน)")
        else:
            sim_balance = max(0, principal_current)
            days_diff = (target_date - as_of_date).days
            sim_interest_new = sim_balance * (annual_rate / 100.0) * (days_diff / 365.0)
            total_interest = accrued_interest_input + sim_interest_new
            est_total = sim_balance + total_interest
            
            st.info(f"📅 ณ วันที่ {target_date.strftime('%d/%m/%Y')} (อีก {days_diff} วันข้างหน้า)")
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("เงินต้นคงเหลือ", f"{sim_balance:,.2f} บาท")
            col_b.metric("ดอกเบี้ยสะสมทั้งหมด", f"{total_interest:,.2f} บาท")
            col_c.metric("ยอดหนี้รวมทั้งสิ้น", f"{est_total:,.2f} บาท")

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
                    "วันที่สิ้นเดือน": next_end_date.strftime('%d/%m/%Y'),
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
                
                chart_ratio_df = pd.DataFrame({
                    "ประเภท": ["เงินต้นรวม", "ดอกเบี้ยรวม"],
                    "จำนวนเงิน (บาท)": [total_principal_paid, total_interest_paid]
                }).set_index("ประเภท")
                st.bar_chart(chart_ratio_df)

with tab3:
    st.subheader("คำนวณงวดต่อเดือนให้หมดหนี้ตามกำหนด (ทุกสิ้นเดือน)")
    target_months = st.number_input("ระยะเวลาที่ต้องการ (เดือน)", value=12, step=1, key="inp_months")
    
    if st.button("คำนวณค่างวดและแสดงตาราง", key="btn3"):
        monthly_rate = (annual_rate / 100) / 12
        bal_target = max(0, principal_current)
        
        if bal_target <= 0 and accrued_interest_input <= 0:
            st.success("คุณไม่มีหนี้คงเหลือแล้วครับ!")
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
                    "วันที่สิ้นเดือน": next_end_date.strftime('%d/%m/%Y'),
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
                
            
