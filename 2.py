import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("📊 评论分析看板")

uploaded_file = st.file_uploader("请上传分析好的 Excel 文件（含3个工作表：近半年、近一年、近两年）", type="xlsx")

if uploaded_file:
    df_半年 = pd.read_excel(uploaded_file, sheet_name='近半年数据分析')
    df_一年 = pd.read_excel(uploaded_file, sheet_name='近一年数据分析')
    df_两年 = pd.read_excel(uploaded_file, sheet_name='近两年数据分析')

    def normalize_satisfaction(s):
        return (s + 5) / 10

    def create_traces(df, period_name):
        avg_importance = df['重要度'].mean()
        norm_satis = normalize_satisfaction(df['满意度'])
        traces = []
        unique_points = df['体验点'].unique()
        sizeref = 2. * max(df['分歧度']) / (40. ** 2)

        for point in unique_points:
            df_sub = df[df['体验点'] == point]
            norm_satis_sub = normalize_satisfaction(df_sub['满意度'])
            trace = go.Scatter(
                x=df_sub['重要度'],
                y=df_sub['满意度'],
                mode='markers+text',
                text=df_sub['体验点'],
                textposition='top center',
                marker=dict(
                    size=df_sub['分歧度'],
                    sizemode='area',
                    sizeref=sizeref,
                    sizemin=4,
                    color=norm_satis_sub,
                    coloraxis='coloraxis',
                    line=dict(width=1, color='DarkSlateGrey')
                ),
                name=point,
                legendgroup=point,
                visible=False,
                hovertemplate=(
                    "体验点: %{text}<br>" +
                    "重要度: %{x}<br>" +
                    "满意度: %{y}<br>" +
                    "分歧度: %{marker.size}<extra></extra>"
                )
            )
            traces.append(trace)
        return traces, avg_importance

    traces_半年, avg_半年 = create_traces(df_半年, '近半年')
    traces_一年, avg_一年 = create_traces(df_一年, '近一年')
    traces_两年, avg_两年 = create_traces(df_两年, '近两年')
    all_traces = traces_半年 + traces_一年 + traces_两年

    fig = go.Figure(data=all_traces)
    for i in range(len(traces_半年)):
        fig.data[i].visible = True

    def create_reference_shapes(avg_importance, df):
        return [
            dict(type='line', x0=df['重要度'].min(), x1=df['重要度'].max(), y0=0, y1=0,
                 line=dict(color='lightgray', width=2, dash='dash')),
            dict(type='line', x0=avg_importance, x1=avg_importance, y0=df['满意度'].min(), y1=df['满意度'].max(),
                 line=dict(color='lightgray', width=2, dash='dash'))
        ]

    def create_annotations(avg_importance, df):
        return [
            dict(x=avg_importance, y=df['满意度'].max(), text=f"重要度均值: {avg_importance:.2f}",
                 showarrow=True, arrowhead=1, ax=40, ay=0),
            dict(x=df['重要度'].max(), y=0, text="满意度 = 0",
                 showarrow=True, arrowhead=1, ax=0, ay=40)
        ]

    fig.update_layout(
        shapes=create_reference_shapes(avg_半年, df_半年),
        annotations=create_annotations(avg_半年, df_半年)
    )

    # 切换按钮
    buttons = []
    lens = [len(traces_半年), len(traces_一年), len(traces_两年)]
    dfs = [df_半年, df_一年, df_两年]
    avgs = [avg_半年, avg_一年, avg_两年]

    start_idx = 0
    for i, label in enumerate(['近半年', '近一年', '近两年']):
        vis = [False] * len(all_traces)
        for j in range(lens[i]):
            vis[start_idx + j] = True
        buttons.append(dict(
            label=label,
            method='update',
            args=[
                {'visible': vis},
                {
                    'shapes': create_reference_shapes(avgs[i], dfs[i]),
                    'annotations': create_annotations(avgs[i], dfs[i])
                }
            ]
        ))
        start_idx += lens[i]

    # 图例说明文字
    fig.add_annotation(
        text="📘 图例说明：\n颜色表示满意度（-5 至 5）\n气泡大小表示分歧度（越大越分歧）",
        xref="paper", yref="paper",
        x=1.02, y=0.4,
        showarrow=False,
        align="left",
        font=dict(size=11),
        bordercolor="gray",
        borderwidth=1,
        bgcolor="white",
        opacity=0.9
    )

    fig.update_layout(
        updatemenus=[
            dict(
                buttons=buttons,
                active=0,
                x=0.98, y=1.12,
                xanchor='right',
                yanchor='top',
                direction='down',
                showactive=True
            )
        ],
        title='体验点气泡图（时间范围切换）',
        xaxis_title='重要度',
        yaxis_title='满意度',
        xaxis=dict(showgrid=False),  # ✅ 关闭 X 网格线
        yaxis=dict(showgrid=False),  # ✅ 关闭 Y 网格线
        plot_bgcolor='white',
        height=800,
        width=1200,
        margin=dict(l=100, r=250, t=100, b=60),
        coloraxis=dict(
            colorscale='balance',
            colorbar=dict(
                title="满意度",
                tickvals=[0, 0.5, 1],
                ticktext=['-5', '0', '5'],
                len=0.7,
                thickness=15,
                outlinewidth=0,
                y=0.5,
                yanchor='middle',
                x=1.35,
                xanchor='left'
            ),
            cmin=0,
            cmax=1,
        ),
        legend=dict(
            title='体验点',
            traceorder='normal',
            bgcolor='rgba(255,255,255,0.95)',
            bordercolor='lightgray',
            borderwidth=1,
            x=1.02,
            y=0.99,
            xanchor='left',
            yanchor='top',
            font=dict(size=11),
            itemsizing='constant',
            valign='top',
            orientation='v'
        )
    )

    # 展示图表
    st.plotly_chart(fig, use_container_width=True)
 
