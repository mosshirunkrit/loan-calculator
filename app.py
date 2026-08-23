import pandas as pd
import numpy_financial as npf
import streamlit as st
from datetime import timedelta

st.set_page_config(page_title="เครื่องมือคำนวณสินเชื่อลดต้นลดดอก", page_icon="💰", layout="centered")

st.title("💰 คำนวณสินเชื่อลดต้นลดดอก")
st.write("เครื่องมือคำนวณยอดหนี้ ประวัติการชำระ และวางแผนอนาคต")

# --- 1. ข้อมูลตั้งต้น ---
st.header("1. ข้อมูลตั้งต้นสัญญา")
col1, col2 = st.columns(2)
with col1:
    principal_start = st.number_input("ยอดเงินต้นเริ่มต้น (บาท)", value=100000.0, step=1000.0, format="%.2f")
with col2:
    # ปรับตรงนี้ให้รับและแสดงผลทศนิยม 3 ตำแหน่ง
    annual_rate = st.number_input("ดอกเบี้ย (% ต่อปี)", value=15.000, step=0.001, format="%.3f")

start_date = st.date_input("วันที่เริ่มกู้สัญญา")

# --- 2. ประวัติการชำระย้อนหลัง ---
st.header("2. ประวัติการชำระหนี้ (ย้อนหลัง)")
st.write("เพิ่มรายการวันที่และยอดเงินที่เคยจ่ายจริง ระบบจะคำนวณตารางตัดชำระให้อัตโนมัติ")

if 'payment_history' not in st.session_state:
    st.session_state.payment_history = pd.DataFrame(columns=["วันที่ชำระ", "ยอดที่ชำระ (บาท)"])

with st.form("add_payment", clear_on_submit=True):
    p_date = st.date_input("วันที่ชำระจริง")
    p_amount = st.number_input("ยอดที่ชำระ (บาท)", min_value=0.0, step=100.0, format="%.2f")
    submitted = st.form_submit_button("➕ เพิ่มประวัติการชำระ")
    if submitted:
        new_row = pd.DataFrame({"วันที่ชำระ": [p_date], "ยอดที่ชำระ (บาท)": [p_amount]})
        st.session_state.payment_history = pd.concat([st.session_state.payment_history, new_row], ignore_index=True)

if not st.session_state.payment_history.empty:
    if st.button("🗑️ ล้างประวัติทั้งหมด"):
        st.session_state.payment_history = pd.DataFrame(columns=["วันที่ชำระ", "ยอดที่ชำระ (บาท)"])
        st.rerun()

# --- คำนวณจำลองยอดหนี้และสร้างตารางประวัติ ---
current_balance = principal_start
schedule_data = []

schedule_data.append({
    "งวดที่": 0,
    "วันที่": start_date,
    "ยอดที่ชำระ": 0.0,
    "จำนวนวัน": 0,
    "ดอกเบี้ย": 0.0,
    "ตัดเงินต้น": 0.0,
    "เงินต้นคงเหลือ": principal_start
})

if not st.session_state.payment_history.empty:
    df_hist = st.session_state.payment_history.sort_values("วันที่ชำระ").reset_index(drop=True)
    prev_d = start_date
    
    for i, row in df_hist.iterrows():
        pay_d = row["วันที่ชำระ"]
        pay_amt = row["ยอดที่ชำระ (บาท)"]
        
        days = (pay_d - prev_d).days
        interest = 0.0
        principal_paid = 0.0
        
        if days > 0 and current_balance > 0:
            interest = current_balance * (annual_rate / 100.0) * (days / 365.0)
            principal_paid = pay_amt - interest
            if principal_paid < 0:
                principal_paid = 0
            current_balance -= principal_paid
        elif current_balance <= 0:
            current_balance = 0
            principal_paid = 0
            
        schedule_data.append({
            "งวดที่": i + 1,
            "วันที่": pay_d,
            "ยอดที่ชำระ": pay_amt,
            "จำนวนวัน": max(0, days),
            "ดอกเบี้ย": round(interest, 2),
            "ตัดเงินต้น": round(principal_paid, 2),
            "เงินต้นคงเหลือ": round(max(0, current_balance), 2)
        })
        prev_d = pay_d

df_schedule = pd.DataFrame(schedule_data)

st.subheader("📊 ตารางประวัติการชำระและยอดหนี้ปัจจุบัน")
st.dataframe(df_schedule, use_container_width=True)

st.success(f"📌 **ยอดหนี้คงเหลือปัจจุบันโดยประมาณ:** {max(0, current_balance):,.2f} บาท")

# --- 3. การคำนวณวางแผนอนาคต ---
st.header("3. คำนวณวางแผนอนาคต")
tab1, tab2, tab3 = st.tabs(["🔮 หนี้คงเหลือในอนาคต", "⏳ ระยะเวลาหมดหนี้", "💵 ค่างวดที่ต้องส่ง"])

# --- Tab 1: หนี้คงเหลือในอนาคตตามวันที่ระบุ ---
with tab1:
    st.subheader("คำนวณยอดหนี้ตามวันที่ระบุในอนาคต")
    target_date = st.date_input("เลือกวันที่ต้องการเช็คยอดหนี้ (ในอนาคต)")
    
    if st.button("คำนวณยอดหนี้ ณ วันที่เลือก", key="btn1"):
        last_date = df_schedule.iloc[-1]["วันที่"]
        if target_date <= last_date:
            st.error("กรุณาเลือกวันที่อยู่ในอนาคต (มากกว่าประวัติการชำระล่าสุด)")
        else:
            sim_balance = current_balance
            days_diff = (target_date - last_date).days
            sim_interest = sim_balance * (annual_rate / 100.0) * (days_diff / 365.0)
            est_total = sim_balance + sim_interest
            
            st.info(f"📅 ณ วันที่ {target_date.strftime('%d/%m/%Y')} (อีก {days_diff} วันข้างหน้า)")
            col_a, col_b = st.columns(2)
            col_a.metric("เงินต้นคงเหลือประมาณ", f"{sim_balance:,.2f} บาท")
            col_b.metric("ดอกเบี้ยสะสมโดยประมาณ", f"{sim_interest:,.2f} บาท")
            st.warning(f"💡 ยอดหนี้รวมทั้งสิ้นโดยประมาณ: **{est_total:,.2f} บาท** (หากยังไม่มียอดชำระเพิ่ม)")

# --- Tab 2: ส่งยอดเท่านี้... อีกนานไหมถึงหมด พร้อมตาราง ---
with tab2:
    st.subheader("แผนผ่อนชำระด้วยยอดคงที่ต่อเดือน")
    fixed_pmt = st.number_input("จำนวนเงินที่จะผ่อนต่อเดือน (บาท)", value=5000.0, step=500.0, format="%.2f", key="inp_pmt")
    
    if st.button("คำนวณระยะเวลาและแสดงตาราง", key="btn2"):
        monthly_rate = (annual_rate / 100) / 12
        if monthly_rate > 0 and fixed_pmt <= current_balance * monthly_rate:
            st.error("ยอดผ่อนต่อเดือนน้อยเกินไป ไม่สามารถหักล้างดอกเบี้ยรายเดือนได้ หนี้จะไม่มีวันหมด")
        elif current_balance <= 0:
            st.success("คุณไม่มีหนี้คงเหลือแล้วครับ!")
        else:
            temp_balance = current_balance
            future_schedule = []
            sim_date = df_schedule.iloc[-1]["วันที่"]
            
            month_count = 0
            while temp_balance > 0 and month_count < 360:
                month_count += 1
                sim_date = sim_date + timedelta(days=30)
                
                interest_m = temp_balance * (annual_rate / 100.0) * (30 / 365.0)
                principal_m = fixed_pmt - interest_m
                
                if principal_m > temp_balance:
                    principal_m = temp_balance
                    actual_pay = temp_balance + interest_m
                else:
                    actual_pay = fixed_pmt
                    
                temp_balance -= principal_m
                if temp_balance < 0: temp_balance = 0
                
                future_schedule.append({
                    "งวดที่": month_count,
                    "วันที่คาดว่าจะจ่าย": sim_date.strftime('%d/%m/%Y'),
                    "ยอดที่ต้องจ่าย": round(actual_pay, 2),
                    "ดอกเบี้ย": round(interest_m, 2),
                    "ตัดเงินต้น": round(principal_m, 2),
                    "เงินต้นคงเหลือ": round(temp_balance, 2)
                })
                
                if temp_balance == 0:
                    break
            
            years = month_count // 12
            rem_m = month_count % 12
            st.warning(f"⏳ จะต้องผ่อนประมาณ **{years} ปี {rem_m} เดือน** ถึงจะหมดหนี้")
            
            st.write("📋 **ตารางจำลองการผ่อนชำระในอนาคต:**")
            st.dataframe(pd.DataFrame(future_schedule), use_container_width=True)

# --- Tab 3: อยากหมดหนี้ในเวลาที่กำหนด... ต้องส่งเดือนละเท่าไร พร้อมตาราง ---
with tab3:
    st.subheader("คำนวณค่างวดรายเดือนเพื่อให้หมดหนี้ตามกำหนด")
    target_months = st.number_input("ระยะเวลาที่ต้องการ (เดือน)", value=12, step=1, key="inp_months")
    
    if st.button("คำนวณค่างวดและแสดงตาราง", key="btn3"):
        monthly_rate = (annual_rate / 100) / 12
        if current_balance <= 0:
            st.success("คุณไม่มีหนี้คงเหลือแล้วครับ!")
        else:
            if monthly_rate > 0:
                pmt_calc = npf.pmt(monthly_rate, target_months, -current_balance)
            else:
                pmt_calc = current_balance / target_months
                
            st.success(f"💵 คุณต้องส่งงวดละประมาณ **{pmt_calc:,.2f} บาท** ทุกเดือน เป็นเวลา {target_months} เดือน")
            
            temp_balance = current_balance
            future_schedule_2 = []
            sim_date = df_schedule.iloc[-1]["วันที่"]
            
            for m in range(1, int(target_months) + 1):
                if temp_balance <= 0: break
                sim_date = sim_date + timedelta(days=30)
                
                interest_m = temp_balance * (annual_rate / 100.0) * (30 / 365.0)
                principal_m = pmt_calc - interest_m
                
                if m == target_months or principal_m > temp_balance:
                    principal_m = temp_balance
                    actual_pay = temp_balance + interest_m
                else:
                    actual_pay = pmt_calc
                    
                temp_balance -= principal_m
                if temp_balance < 0: temp_balance = 0
                
                future_schedule_2.append({
                    "งวดที่": m,
                    "วันที่คาดว่าจะจ่าย": sim_date.strftime('%d/%m/%Y'),
                    "ยอดที่ต้องจ่าย": round(actual_pay, 2),
                    "ดอกเบี้ย": round(interest_m, 2),
                    "ตัดเงินต้น": round(principal_m, 2),
                    "เงินต้นคงเหลือ": round(temp_balance, 2)
                })
                
            st.write("📋 **ตารางจำลองการผ่อนชำระตามระยะเวลาที่กำหนด:**")
            st.dataframe(pd.DataFrame(future_schedule_2), use_container_width=True)
