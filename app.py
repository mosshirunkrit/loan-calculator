import pandas as pd
import numpy_financial as npf
import streamlit as st
from datetime import timedelta

st.set_page_config(page_title="เครื่องมือคำนวณสินเชื่อลดต้นลดดอก", page_icon="💰", layout="centered")

st.title("💰 คำนวณสินเชื่อลดต้นลดดอก (รอบบิลสิ้นเดือน)")
st.write("เครื่องมือตรวจสอบประวัติย้อนหลัง และวางแผนชำระหนี้ทุกสิ้นเดือน")

# --- ฟังก์ชันช่วยคำนวณวันสิ้นเดือนถัดไป ---
def get_next_end_of_month(current_date):
    # ขยับไปวันที่ 1 ของเดือนถัดไป แล้วลบออก 1 วัน จะได้วันสิ้นเดือนพอดี
    next_month_first = (current_date.replace(day=1) + timedelta(days=32)).replace(day=1)
    return next_month_first - timedelta(days=1)

# --- เลือกโหมดการคำนวณ ---
st.header("1. เลือกรูปแบบการคำนวณย้อนหลัง")
calc_mode = st.radio(
    "เลือกวิธีตั้งต้นข้อมูล:",
    ["เดินหน้าจากยอดวันแรก (Forward)", "แกะรอยย้อนกลับจากยอดหนี้ปัจจุบัน (Backward Audit)"]
)

# --- ข้อมูลตั้งต้นตามโหมด ---
st.header("2. ข้อมูลตั้งต้นสัญญา")
col1, col2 = st.columns(2)
with col1:
    if calc_mode == "เดินหน้าจากยอดวันแรก (Forward)":
        principal_input = st.number_input("ยอดเงินต้นเริ่มต้น (วันแรก)", value=100000.0, step=1000.0, format="%.2f")
    else:
        principal_input = st.number_input("ยอดหนี้ปัจจุบัน (ตั้งต้นเพื่อแกะย้อนหลัง)", value=95000.0, step=1000.0, format="%.2f")
with col2:
    annual_rate = st.number_input("ดอกเบี้ย (% ต่อปี)", value=15.000, step=0.001, format="%.3f")

base_date = st.date_input("วันที่อ้างอิงเริ่มต้น")

# --- ประวัติการชำระ ---
st.header("3. ประวัติการชำระหนี้")
if calc_mode == "เดินหน้าจากยอดวันแรก (Forward)":
    st.write("ใส่ประวัติการจ่ายเงินตามลำดับเวลาจริง (จากอดีตมาปัจจุบัน)")
else:
    st.write("ใส่ประวัติการจ่ายเงินที่เคยจ่ายไป เพื่อให้ระบบคำนวณย้อนกลับไปดูยอดหนี้ก่อนหน้านั้น")

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

schedule_data = []
current_balance_result = 0.0

# ================= โหมดที่ 1: เดินหน้า (Forward) =================
if calc_mode == "เดินหน้าจากยอดวันแรก (Forward)":
    current_balance = principal_input
    schedule_data.append({
        "งวดที่": 0,
        "วันที่": base_date,
        "ยอดที่ชำระ": 0.0,
        "จำนวนวัน": 0,
        "ดอกเบี้ย": 0.0,
        "ตัดเงินต้น": 0.0,
        "เงินต้นคงเหลือ": principal_input
    })
    
    if not st.session_state.payment_history.empty:
        df_hist = st.session_state.payment_history.sort_values("วันที่ชำระ").reset_index(drop=True)
        prev_d = base_date
        
        for i, row in df_hist.iterrows():
            pay_d = row["วันที่ชำระ"]
            pay_amt = row["ยอดที่ชำระ (บาท)"]
            days = (pay_d - prev_d).days
            
            interest = 0.0
            principal_paid = 0.0
            if days > 0 and current_balance > 0:
                interest = current_balance * (annual_rate / 100.0) * (days / 365.0)
                principal_paid = pay_amt - interest
                if principal_paid < 0: principal_paid = 0
                current_balance -= principal_paid
            elif current_balance <= 0:
                current_balance = 0
                
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
    current_balance_result = current_balance

# ================= โหมดที่ 2: ย้อนกลับ (Backward Audit) =================
else:
    if st.session_state.payment_history.empty:
        st.warning("⚠️ กรุณาเพิ่มประวัติการชำระอย่างน้อย 1 รายการ เพื่อให้ระบบคำนวณย้อนกลับจากยอดปัจจุบัน")
        current_balance_result = principal_input
        schedule_data.append({
            "งวดที่": 0,
            "วันที่": base_date,
            "ยอดที่ชำระ": 0.0,
            "จำนวนวัน": 0,
            "ดอกเบี้ย": 0.0,
            "ตัดเงินต้น": 0.0,
            "เงินต้นคงเหลือ": principal_input
        })
    else:
        df_hist = st.session_state.payment_history.sort_values("วันที่ชำระ", ascending=False).reset_index(drop=True)
        running_balance = principal_input
        temp_rows = []
        next_d = base_date
        
        for i, row in df_hist.iterrows():
            pay_d = row["วันที่ชำระ"]
            pay_amt = row["ยอดที่ชำระ (บาท)"]
            days = (next_d - pay_d).days
            
            if days > 0:
                approx_interest = running_balance * (annual_rate / 100.0) * (days / 365.0)
                prev_balance = running_balance + pay_amt - approx_interest
                if prev_balance < 0: prev_balance = 0
                
                exact_interest = prev_balance * (annual_rate / 100.0) * (days / 365.0)
                principal_part = pay_amt - exact_interest
                if principal_part < 0: principal_part = 0
                
                temp_rows.append({
                    "วันที่ชำระ": pay_d,
                    "ยอดที่ชำระ": pay_amt,
                    "จำนวนวันย้อนหลัง": days,
                    "ดอกเบี้ยช่วงนั้น": round(exact_interest, 2),
                    "ตัดเงินต้น": round(principal_part, 2),
                    "ยอดหนี้ก่อนจ่าย": round(prev_balance, 2)
                })
                running_balance = prev_balance
                next_d = pay_d
            else:
                temp_rows.append({
                    "วันที่ชำระ": pay_d,
                    "ยอดที่ชำระ": pay_amt,
                    "จำนวนวันย้อนหลัง": 0,
                    "ดอกเบี้ยช่วงนั้น": 0.0,
                    "ตัดเงินต้น": pay_amt,
                    "ยอดหนี้ก่อนจ่าย": round(running_balance, 2)
                })
        
        schedule_data.append({
            "งวดที่": 0,
            "วันที่": next_d,
            "ยอดที่ชำระ": 0.0,
            "จำนวนวัน": 0,
            "ดอกเบี้ย": 0.0,
            "ตัดเงินต้น": 0.0,
            "เงินต้นคงเหลือ": round(running_balance, 2)
        })
        
        temp_rows.reverse()
        for idx, r in enumerate(temp_rows):
            schedule_data.append({
                "งวดที่": idx + 1,
                "วันที่": r["วันที่ชำระ"],
                "ยอดที่ชำระ": r["ยอดที่ชำระ"],
                "จำนวนวัน": r["จำนวนวันย้อนหลัง"],
                "ดอกเบี้ย": r["ดอกเบี้ยช่วงนั้น"],
                "ตัดเงินต้น": r["ตัดเงินต้น"],
                "เงินต้นคงเหลือ": r["ยอดหนี้ก่อนจ่าย"]
            })
        current_balance_result = principal_input

df_schedule = pd.DataFrame(schedule_data)

st.subheader("📊 ตารางตรวจสอบประวัติและดอกเบี้ย")
st.dataframe(df_schedule, use_container_width=True)

if calc_mode == "เดินหน้าจากยอดวันแรก (Forward)":
    st.success(f"📌 **ยอดหนี้คงเหลือปัจจุบัน:** {max(0, current_balance_result):,.2f} บาท")
else:
    st.info(f"📌 **ยอดหนี้ตั้งต้นปัจจุบันที่ใช้คำนวณ:** {principal_input:,.2f} บาท")

# --- 4. การคำนวณวางแผนอนาคต (ตัดรอบทุกสิ้นเดือน) ---
st.header("4. คำนวณวางแผนอนาคต (รอบสิ้นเดือน)")
tab1, tab2, tab3 = st.tabs(["🔮 หนี้คงเหลือในอนาคต", "⏳ ระยะเวลาหมดหนี้", "💵 ค่างวดที่ต้องส่ง"])

# กำหนดจุดตั้งต้นวันที่ใช้คำนวณต่อในอนาคต (อิงจากประวัติล่าสุด)
last_record_date = df_schedule.iloc[-1]["วันที่"] if not df_schedule.empty else base_date

with tab1:
    st.subheader("คำนวณยอดหนี้ตามวันที่ระบุในอนาคต")
    target_date = st.date_input("เลือกวันที่ต้องการเช็คยอดหนี้ (ในอนาคต)")
    
    if st.button("คำนวณยอดหนี้ ณ วันที่เลือก", key="btn1"):
        if target_date <= last_record_date:
            st.error("กรุณาเลือกวันที่อยู่ในอนาคต (หลังจากประวัติล่าสุด)")
        else:
            sim_balance = max(0, current_balance_result)
            days_diff = (target_date - last_record_date).days
            sim_interest = sim_balance * (annual_rate / 100.0) * (days_diff / 365.0)
            est_total = sim_balance + sim_interest
            
            st.info(f"📅 ณ วันที่ {target_date.strftime('%d/%m/%Y')} (อีก {days_diff} วัน)")
            col_a, col_b = st.columns(2)
            col_a.metric("เงินต้นคงเหลือ", f"{sim_balance:,.2f} บาท")
            col_b.metric("ดอกเบี้ยสะสม", f"{sim_interest:,.2f} บาท")
            st.warning(f"💡 ยอดหนี้รวมทั้งสิ้น: **{est_total:,.2f} บาท**")

with tab2:
    st.subheader("แผนผ่อนชำระด้วยยอดคงที่ต่อเดือน (ทุกสิ้นเดือน)")
    fixed_pmt = st.number_input("จำนวนเงินที่จะผ่อนต่อเดือน (บาท)", value=5000.0, step=500.0, format="%.2f", key="inp_pmt")
    
    if st.button("คำนวณระยะเวลาและแสดงตาราง", key="btn2"):
        monthly_rate = (annual_rate / 100) / 12
        bal_target = max(0, current_balance_result)
        if monthly_rate > 0 and fixed_pmt <= bal_target * monthly_rate:
            st.error("ยอดผ่อนต่อเดือนน้อยเกินไป ไม่สามารถหักล้างดอกเบี้ยรายเดือนได้ หนี้จะไม่มีวันหมด")
        elif bal_target <= 0:
            st.success("หมดหนี้แล้วครับ!")
        else:
            temp_balance = bal_target
            future_schedule = []
            
            # เริ่มต้นนับรอบจากประวัติล่าสุด ไปยังวันสิ้นเดือนถัดไป
            sim_date = last_record_date
            month_count = 0
            
            while temp_balance > 0 and month_count < 360:
                month_count += 1
                next_end_date = get_next_end_of_month(sim_date)
                days_m = (next_end_date - sim_date).days
                
                # คำนวณดอกเบี้ยตามจำนวนวันจริงจนถึงวันสิ้นเดือน
                interest_m = temp_balance * (annual_rate / 100.0) * (days_m / 365.0)
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
                    "วันที่สิ้นเดือน": next_end_date.strftime('%d/%m/%Y'),
                    "จำนวนวัน": days_m,
                    "ยอดที่ต้องจ่าย": round(actual_pay, 2),
                    "ดอกเบี้ย": round(interest_m, 2),
                    "ตัดเงินต้น": round(principal_m, 2),
                    "เงินต้นคงเหลือ": round(temp_balance, 2)
                })
                
                sim_date = next_end_date
                if temp_balance == 0: break
            
            years = month_count // 12
            rem_m = month_count % 12
            st.warning(f"⏳ จะต้องผ่อนประมาณ **{years} ปี {rem_m} เดือน** ถึงจะหมดหนี้")
            st.dataframe(pd.DataFrame(future_schedule), use_container_width=True)

with tab3:
    st.subheader("คำนวณค่างวดรายเดือนเพื่อให้หมดหนี้ตามกำหนด (ทุกสิ้นเดือน)")
    target_months = st.number_input("ระยะเวลาที่ต้องการ (เดือน)", value=12, step=1, key="inp_months")
    
    if st.button("คำนวณค่างวดและแสดงตาราง", key="btn3"):
        monthly_rate = (annual_rate / 100) / 12
        bal_target = max(0, current_balance_result)
        if bal_target <= 0:
            st.success("หมดหนี้แล้วครับ!")
        else:
            if monthly_rate > 0:
                pmt_calc = npf.pmt(monthly_rate, target_months, -bal_target)
            else:
                pmt_calc = bal_target / target_months
                
            st.success(f"💵 ต้องส่งงวดละประมาณ **{pmt_calc:,.2f} บาท** ทุกสิ้นเดือน เป็นเวลา {target_months} เดือน")
            
            temp_balance = bal_target
            future_schedule_2 = []
            sim_date = last_record_date
            
            for m in range(1, int(target_months) + 1):
                if temp_balance <= 0: break
                next_end_date = get_next_end_of_month(sim_date)
                days_m = (next_end_date - sim_date).days
                
                interest_m = temp_balance * (annual_rate / 100.0) * (days_m / 365.0)
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
                    "วันที่สิ้นเดือน": next_end_date.strftime('%d/%m/%Y'),
                    "จำนวนวัน": days_m,
                    "ยอดที่ต้องจ่าย": round(actual_pay, 2),
                    "ดอกเบี้ย": round(interest_m, 2),
                    "ตัดเงินต้น": round(principal_m, 2),
                    "เงินต้นคงเหลือ": round(temp_balance, 2)
                })
                sim_date = next_end_date
                
            st.dataframe(pd.DataFrame(future_schedule_2), use_container_width=True)
