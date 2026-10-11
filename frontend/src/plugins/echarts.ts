import * as echarts from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import {
  BarChart,
  LineChart,
  PieChart,
  MapChart,
  ScatterChart,
  EffectScatterChart,
  LinesChart,
} from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  ToolboxComponent,
  DataZoomComponent,
  GeoComponent,
  VisualMapComponent,
} from 'echarts/components';
// 1. Register all core ECharts renderers, charts, and components first
echarts.use([
  CanvasRenderer,
  BarChart,
  LineChart,
  PieChart,
  MapChart,
  ScatterChart,
  EffectScatterChart,
  LinesChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  ToolboxComponent,
  DataZoomComponent,
  GeoComponent,
  VisualMapComponent,
]);

export default echarts;


