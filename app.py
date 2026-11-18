import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="Bank Customer Dashboard", layout="wide")
st.title("🏦 은행 고객 이탈 분석 대시보드")

INCOME_LABELS = {
    0: "자료없음",
    1: "4천만원 미만",
    2: "4천~6천만원",
    3: "6천~8천만원",
    4: "8천만~1억2천",
    5: "1억2천 초과",
}

# 2. 데이터 불러오기
@st.cache_data
def load_data():
    df = pd.read_excel("bank_customer.xlsx", sheet_name="bank_customer")
    df = df.dropna()
    df["Income_Label"] = df["Income_Category"].map(INCOME_LABELS)
    return df

try:
    df = load_data()

    # 3. 사이드바 필터
    st.sidebar.header("필터 옵션")
    cards = ["전체"] + ["Blue", "Silver", "Gold", "Platinum"]
    selected_card = st.sidebar.selectbox("카드 등급을 선택하세요:", cards)
    genders = st.sidebar.multiselect("성별:", sorted(df["Gender"].unique()),
                                     default=sorted(df["Gender"].unique()))

    filtered_df = df[df["Gender"].isin(genders)]
    if selected_card != "전체":
        filtered_df = filtered_df[filtered_df["Card_Category"] == selected_card]

    if filtered_df.empty:
        st.warning("선택한 조건에 해당하는 고객이 없습니다.")
        st.stop()

    # 4. KPI
    total_customers = len(filtered_df)
    churn_rate = (filtered_df["Attrition_Flag"] == "이탈").mean() * 100
    avg_limit = filtered_df["Credit_Limit"].mean()
    avg_trans = filtered_df["Total_Trans_Amt"].mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("고객 수", f"{total_customers:,}명")
    c2.metric("이탈률", f"{churn_rate:.1f}%")
    c3.metric("평균 신용한도", f"${avg_limit:,.0f}")
    c4.metric("평균 거래금액", f"${avg_trans:,.0f}")

    st.markdown("---")

    left, right = st.columns(2)

    # 5. 연소득 수준별 이탈률
    with left:
        st.subheader("📊 연소득 수준별 이탈률")
        income = (filtered_df.groupby(["Income_Category", "Income_Label"])["Attrition_Flag"]
                  .apply(lambda s: (s == "이탈").mean() * 100)
                  .reset_index(name="이탈률")
                  .sort_values("Income_Category"))
        fig1 = px.bar(income, x="Income_Label", y="이탈률", text_auto=".1f",
                      labels={"Income_Label": "연소득 수준", "이탈률": "이탈률 (%)"},
                      color="이탈률", color_continuous_scale="Reds")
        st.plotly_chart(fig1, use_container_width=True)

    # 6. 유지/이탈 고객 비율
    with right:
        st.subheader("🥧 유지 vs 이탈 고객 비율")
        flag = filtered_df["Attrition_Flag"].value_counts().reset_index()
        flag.columns = ["구분", "고객 수"]
        fig2 = px.pie(flag, names="구분", values="고객 수", hole=0.4,
                      color="구분", color_discrete_map={"유지": "#2563eb", "이탈": "#ef4444"})
        st.plotly_chart(fig2, use_container_width=True)

    # 7. 거래금액 분포 (유지 vs 이탈)
    st.subheader("💳 유지/이탈 고객의 거래금액 분포")
    fig3 = px.box(filtered_df, x="Attrition_Flag", y="Total_Trans_Amt", color="Attrition_Flag",
                  labels={"Attrition_Flag": "고객 구분", "Total_Trans_Amt": "거래금액 ($)"},
                  color_discrete_map={"유지": "#2563eb", "이탈": "#ef4444"})
    st.plotly_chart(fig3, use_container_width=True)

    with st.expander("원본 데이터 보기"):
        st.dataframe(filtered_df.drop(columns=["Income_Label"]))

except Exception as e:
    st.error(f"데이터를 로드하는 과정에서 오류가 발생했습니다: {e}")
