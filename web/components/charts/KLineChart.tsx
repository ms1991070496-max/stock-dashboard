"use client";

import { useEffect, useRef } from "react";
import {
  createChart,
  ColorType,
  CrosshairMode,
  type IChartApi,
  type ISeriesApi,
  type CandlestickData,
  type HistogramData,
  type LineData,
  type Time,
} from "lightweight-charts";

interface Props {
  data: {
    dates: string[];
    open: number[];
    high: number[];
    low: number[];
    close: number[];
    volume: number[];
    ma5: (number | null)[];
    ma10: (number | null)[];
    ma20: (number | null)[];
    macd_dif: (number | null)[];
    macd_dea: (number | null)[];
    macd_hist: (number | null)[];
  };
}

export function KLineChart({ data }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!containerRef.current || data.dates.length === 0) return;

    const n = data.dates.length;

    // Build candlestick series
    const candleData: CandlestickData<Time>[] = [];
    const volumeData: HistogramData<Time>[] = [];
    const ma5Data: LineData<Time>[] = [];
    const ma10Data: LineData<Time>[] = [];
    const ma20Data: LineData<Time>[] = [];
    const macdHistData: HistogramData<Time>[] = [];
    const macdDifData: LineData<Time>[] = [];
    const macdDeaData: LineData<Time>[] = [];

    for (let i = 0; i < n; i++) {
      const t = (data.dates[i] as string) as Time;
      candleData.push({
        time: t,
        open: data.open[i],
        high: data.high[i],
        low: data.low[i],
        close: data.close[i],
      });
      volumeData.push({
        time: t,
        value: data.volume[i],
        color:
          data.close[i] >= data.open[i]
            ? "rgba(239, 68, 68, 0.5)"
            : "rgba(34, 197, 94, 0.5)",
      });

      if (data.ma5[i] != null)
        ma5Data.push({ time: t, value: data.ma5[i]! });
      if (data.ma10[i] != null)
        ma10Data.push({ time: t, value: data.ma10[i]! });
      if (data.ma20[i] != null)
        ma20Data.push({ time: t, value: data.ma20[i]! });

      if (data.macd_hist[i] != null)
        macdHistData.push({
          time: t,
          value: data.macd_hist[i]!,
          color:
            data.macd_hist[i]! >= 0
              ? "rgba(239, 68, 68, 0.5)"
              : "rgba(34, 197, 94, 0.5)",
        });
      if (data.macd_dif[i] != null)
        macdDifData.push({ time: t, value: data.macd_dif[i]! });
      if (data.macd_dea[i] != null)
        macdDeaData.push({ time: t, value: data.macd_dea[i]! });
    }

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height: 600,
      layout: {
        background: { type: ColorType.Solid, color: "#0f1117" },
        textColor: "#8890a0",
      },
      grid: {
        vertLines: { color: "#1a1d2e" },
        horzLines: { color: "#1a1d2e" },
      },
      crosshair: { mode: CrosshairMode.Normal },
      timeScale: {
        timeVisible: true,
        borderColor: "#2a2d3e",
      },
      rightPriceScale: {
        borderColor: "#2a2d3e",
      },
    });

    // K-line
    const candleSeries = chart.addCandlestickSeries({
      upColor: "#ef4444",
      downColor: "#22c55e",
      borderUpColor: "#ef4444",
      borderDownColor: "#22c55e",
      wickUpColor: "#ef4444",
      wickDownColor: "#22c55e",
    });
    candleSeries.setData(candleData);

    // MAs
    if (ma5Data.length > 0) {
      const ma5Series = chart.addLineSeries({
        color: "#f59e0b",
        lineWidth: 1,
      });
      ma5Series.setData(ma5Data);
    }
    if (ma10Data.length > 0) {
      const ma10Series = chart.addLineSeries({
        color: "#3b82f6",
        lineWidth: 1,
      });
      ma10Series.setData(ma10Data);
    }
    if (ma20Data.length > 0) {
      const ma20Series = chart.addLineSeries({
        color: "#8b5cf6",
        lineWidth: 1,
      });
      ma20Series.setData(ma20Data);
    }

    // Volume (separate pane)
    const volSeries = chart.addHistogramSeries({
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
    });
    volSeries.setData(volumeData);
    chart.priceScale("volume").applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });

    // MACD (separate pane)
    if (macdDifData.length > 0) {
      const macdHistSeries = chart.addHistogramSeries({
        priceScaleId: "macd",
      });
      macdHistSeries.setData(macdHistData);

      const macdDifSeries = chart.addLineSeries({
        color: "#3b82f6",
        lineWidth: 1,
        priceScaleId: "macd",
      });
      macdDifSeries.setData(macdDifData);

      const macdDeaSeries = chart.addLineSeries({
        color: "#f59e0b",
        lineWidth: 1,
        priceScaleId: "macd",
      });
      macdDeaSeries.setData(macdDeaData);

      chart.priceScale("macd").applyOptions({
        scaleMargins: { top: 0.6, bottom: 0.4 },
      });
    }

    chartRef.current = chart;

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, [data]);

  return <div ref={containerRef} className="w-full" />;
}
