<template>
  <div class="relative w-full max-w-[420px] aspect-[4/3] flex items-center justify-center select-none overflow-visible will-change-transform">
    <!-- Ambient Glow behind illustration (Hardware accelerated) -->
    <div class="absolute inset-0 bg-gradient-to-tr from-sky-500/15 via-indigo-500/10 to-sky-400/15 rounded-full blur-xl pointer-events-none transform scale-90 will-change-transform"></div>

    <!-- Master Vector Illustration Canvas (High Performance 60FPS SVG) -->
    <svg 
      viewBox="0 0 800 560" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      class="w-full h-full overflow-visible"
    >
      <defs>
        <!-- Gradients -->
        <linearGradient id="monitorBodyGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#0f2942" />
          <stop offset="100%" stop-color="#081b2e" />
        </linearGradient>

        <linearGradient id="monitorStandGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#0284c7" />
          <stop offset="100%" stop-color="#0369a1" />
        </linearGradient>

        <linearGradient id="screenGrad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#f8fafc" />
          <stop offset="100%" stop-color="#f1f5f9" />
        </linearGradient>

        <linearGradient id="robotBodyGrad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#38bdf8" />
          <stop offset="100%" stop-color="#0284c7" />
        </linearGradient>

        <linearGradient id="chartSkyGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.45" />
          <stop offset="100%" stop-color="#38bdf8" stop-opacity="0.0" />
        </linearGradient>

        <linearGradient id="folderGrad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#0ea5e9" />
          <stop offset="100%" stop-color="#0284c7" />
        </linearGradient>
      </defs>

      <!-- ================= BACKGROUND FLOATING ELEMENTS ================= -->

      <!-- Background Trade Report Sheet 1 (Top Left) -->
      <g class="animate-float-fast">
        <!-- Shadow Layer -->
        <rect x="144" y="86" width="130" height="180" rx="10" fill="#0f172a" fill-opacity="0.07" />
        <!-- Sheet Body -->
        <rect x="140" y="80" width="130" height="180" rx="10" fill="#ffffff" stroke="#e2e8f0" stroke-width="2" />
        <rect x="155" y="100" width="60" height="8" rx="4" fill="#cbd5e1" />
        <rect x="155" y="116" width="100" height="5" rx="2.5" fill="#e2e8f0" />
        <rect x="155" y="128" width="85" height="5" rx="2.5" fill="#e2e8f0" />
        <rect x="155" y="140" width="95" height="5" rx="2.5" fill="#e2e8f0" />
        
        <!-- Sheet Mini Bar Chart -->
        <g transform="translate(155, 175)">
          <rect x="0" y="35" width="12" height="25" rx="2" fill="#93c5fd" />
          <rect x="18" y="20" width="12" height="40" rx="2" fill="#38bdf8" />
          <rect x="36" y="10" width="12" height="50" rx="2" fill="#0284c7" />
          <rect x="54" y="25" width="12" height="35" rx="2" fill="#38bdf8" />
          <rect x="72" y="5" width="12" height="55" rx="2" fill="#0369a1" />
        </g>
      </g>

      <!-- Background Pie Chart Indicator (Top Center-Left) -->
      <g class="animate-spin-fluid" transform="translate(100, 110)">
        <circle cx="2" cy="4" r="32" fill="#0f172a" fill-opacity="0.08" />
        <circle cx="0" cy="0" r="32" fill="#ffffff" stroke="#e2e8f0" stroke-width="2" />
        <!-- Pie segments -->
        <path d="M 0 0 L 0 -24 A 24 24 0 0 1 24 0 Z" fill="#0284c7" />
        <path d="M 0 0 L 24 0 A 24 24 0 0 1 0 24 Z" fill="#38bdf8" />
        <path d="M 0 0 L 0 24 A 24 24 0 0 1 -24 0 Z" fill="#e2e8f0" />
        <path d="M 0 0 L -24 0 A 24 24 0 0 1 0 -24 Z" fill="#93c5fd" />
        <circle cx="0" cy="0" r="10" fill="#ffffff" />
      </g>

      <!-- Background Trade Report Sheet 2 (Top Right) -->
      <g class="animate-float-alt">
        <rect x="584" y="96" width="140" height="190" rx="10" fill="#0f172a" fill-opacity="0.07" />
        <rect x="580" y="90" width="140" height="190" rx="10" fill="#ffffff" stroke="#e2e8f0" stroke-width="2" />
        <rect x="598" y="110" width="70" height="8" rx="4" fill="#cbd5e1" />
        
        <!-- Mini Header pill -->
        <rect x="598" y="128" width="104" height="24" rx="6" fill="#f0f9ff" stroke="#bae6fd" stroke-width="1.5" />
        <circle cx="612" cy="140" r="4" fill="#0284c7" />
        <rect x="622" y="137" width="50" height="6" rx="3" fill="#0284c7" />

        <!-- Mini Area Wave Chart -->
        <path d="M 598 220 C 620 195, 640 230, 660 185 C 680 210, 690 190, 702 200 L 702 245 L 598 245 Z" fill="url(#chartSkyGrad)" />
        <path d="M 598 220 C 620 195, 640 230, 660 185 C 680 210, 690 190, 702 200" stroke="#0284c7" stroke-width="2.5" stroke-linecap="round" />
        
        <!-- Column Bars -->
        <g transform="translate(598, 225)">
          <rect x="0" y="0" width="8" height="20" rx="2" fill="#38bdf8" />
          <rect x="14" y="-8" width="8" height="28" rx="2" fill="#0284c7" />
          <rect x="28" y="-18" width="8" height="38" rx="2" fill="#0369a1" />
          <rect x="42" y="-10" width="8" height="30" rx="2" fill="#38bdf8" />
          <rect x="56" y="-24" width="8" height="44" rx="2" fill="#0ea5e9" />
          <rect x="70" y="-14" width="8" height="34" rx="2" fill="#0284c7" />
          <rect x="84" y="-4" width="8" height="24" rx="2" fill="#93c5fd" />
          <rect x="96" y="-20" width="8" height="40" rx="2" fill="#0284c7" />
        </g>
      </g>

      <!-- Background Floating Certificate / Document 3 (Bottom Right) -->
      <g class="animate-float-fast">
        <rect x="644" y="325" width="105" height="135" rx="8" fill="#0f172a" fill-opacity="0.06" />
        <rect x="640" y="320" width="105" height="135" rx="8" fill="#ffffff" stroke="#e2e8f0" stroke-width="2" />
        <rect x="655" y="338" width="50" height="6" rx="3" fill="#cbd5e1" />
        <rect x="655" y="350" width="75" height="4" rx="2" fill="#e2e8f0" />
        <rect x="655" y="360" width="65" height="4" rx="2" fill="#e2e8f0" />
        <rect x="655" y="370" width="70" height="4" rx="2" fill="#e2e8f0" />
        <!-- Bottom Mini Bar chart -->
        <rect x="655" y="415" width="8" height="20" rx="2" fill="#38bdf8" />
        <rect x="668" y="405" width="8" height="30" rx="2" fill="#0284c7" />
        <rect x="681" y="395" width="8" height="40" rx="2" fill="#0369a1" />
        <rect x="694" y="410" width="8" height="25" rx="2" fill="#38bdf8" />
      </g>

      <!-- Floating Analytics Coin Disc (Bottom Right) -->
      <g transform="translate(625, 465)" class="animate-bounce-gentle">
        <circle cx="0" cy="0" r="26" fill="#ffffff" stroke="#e2e8f0" stroke-width="2" />
        <rect x="-8" y="-8" width="16" height="16" rx="4" fill="#0284c7" />
        <path d="M -4 0 L -1 3 L 4 -2" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
      </g>

      <!-- ================= LEFT SIDE WORKSPACE ELEMENTS ================= -->

      <!-- Blue Project Folder -->
      <g class="animate-float-alt">
        <!-- Shadow -->
        <path d="M 74 266 L 199 266 C 201 360, 66 360, 74 266 Z" fill="#0f172a" fill-opacity="0.08" />
        <path d="M 80 260 L 120 260 L 135 275 L 185 275 C 190 275, 195 280, 195 285 L 195 345 C 195 352, 190 358, 183 358 L 82 358 C 75 358, 70 352, 70 345 L 70 270 C 70 264, 75 260, 80 260 Z" fill="url(#folderGrad)" />
        <!-- Document coming out of folder -->
        <rect x="85" y="245" width="90" height="60" rx="6" fill="#ffffff" stroke="#bae6fd" stroke-width="1.5" />
        <rect x="95" y="258" width="45" height="5" rx="2.5" fill="#38bdf8" />
        <rect x="95" y="270" width="70" height="4" rx="2" fill="#e2e8f0" />
        <rect x="95" y="280" width="60" height="4" rx="2" fill="#e2e8f0" />
        <!-- Folder Front Lip -->
        <path d="M 70 285 C 70 280, 75 275, 82 275 L 183 275 C 190 275, 195 280, 195 285 L 195 345 C 195 352, 190 358, 183 358 L 82 358 C 75 358, 70 352, 70 345 Z" fill="#0284c7" />
        <circle cx="165" cy="330" r="10" fill="#38bdf8" />
        <path d="M 160 330 L 170 330 M 165 325 L 165 335" stroke="#ffffff" stroke-width="2" stroke-linecap="round" />
      </g>

      <!-- Server Rack Units (Bottom Left) -->
      <g transform="translate(60, 390)">
        <!-- Server 1 -->
        <rect x="0" y="0" width="145" height="26" rx="6" fill="#0f2942" stroke="#1e40af" stroke-width="1.5" />
        <rect x="8" y="7" width="30" height="12" rx="3" fill="#0284c7" />
        <circle cx="115" cy="13" r="3.5" fill="#38bdf8" class="animate-pulse" />
        <circle cx="126" cy="13" r="3.5" fill="#34d399" class="animate-pulse" />
        <circle cx="137" cy="13" r="3.5" fill="#38bdf8" />
        
        <!-- Server 2 -->
        <rect x="0" y="32" width="145" height="26" rx="6" fill="#0f2942" stroke="#1e40af" stroke-width="1.5" />
        <rect x="8" y="39" width="30" height="12" rx="3" fill="#0369a1" />
        <circle cx="115" cy="45" r="3.5" fill="#34d399" class="animate-pulse" />
        <circle cx="126" cy="45" r="3.5" fill="#38bdf8" class="animate-pulse" />
        <circle cx="137" cy="45" r="3.5" fill="#34d399" />

        <!-- Server 3 -->
        <rect x="0" y="64" width="145" height="26" rx="6" fill="#0f2942" stroke="#1e40af" stroke-width="1.5" />
        <rect x="8" y="71" width="30" height="12" rx="3" fill="#0284c7" />
        <circle cx="115" cy="77" r="3.5" fill="#38bdf8" />
        <circle cx="126" cy="77" r="3.5" fill="#34d399" class="animate-pulse" />
        <circle cx="137" cy="77" r="3.5" fill="#38bdf8" class="animate-pulse" />
      </g>


      <!-- ================= CENTER MAIN DESKTOP MONITOR ================= -->

      <!-- Monitor Stand & Base -->
      <g>
        <!-- Stand Pillar -->
        <path d="M 370 410 L 430 410 L 440 480 L 360 480 Z" fill="url(#monitorStandGrad)" />
        <path d="M 370 410 L 400 410 L 395 480 L 360 480 Z" fill="#0284c7" />
        
        <!-- Stand Base Foot Shadow -->
        <ellipse cx="400" cy="508" rx="90" ry="12" fill="#0f172a" fill-opacity="0.12" />
        <!-- Stand Base Foot -->
        <path d="M 320 480 L 480 480 C 490 480, 495 485, 490 492 L 475 500 C 470 504, 460 505, 450 505 L 350 505 C 340 505, 330 504, 325 500 L 310 492 C 305 485, 310 480, 320 480 Z" fill="#082f49" stroke="#0284c7" stroke-width="2" />
        <!-- Base Highlight -->
        <rect x="375" y="488" width="50" height="4" rx="2" fill="#38bdf8" />
      </g>

      <!-- Monitor Bezel & Frame -->
      <g>
        <!-- Frame Shadow -->
        <rect x="236" y="168" width="340" height="260" rx="18" fill="#0f172a" fill-opacity="0.14" />
        <!-- Outer Black/Navy Bezel -->
        <rect x="230" y="160" width="340" height="260" rx="18" fill="url(#monitorBodyGrad)" stroke="#0284c7" stroke-width="3" />
        <!-- Top Webcam & Sensor -->
        <circle cx="400" cy="170" r="3.5" fill="#0284c7" />
        <circle cx="400" cy="170" r="1.5" fill="#38bdf8" />
        <circle cx="415" cy="170" r="1.5" fill="#34d399" class="animate-pulse" />

        <!-- Screen Surface -->
        <rect x="242" y="180" width="316" height="225" rx="8" fill="url(#screenGrad)" />
      </g>

      <!-- ================= MONITOR SCREEN DASHBOARD CONTENT ================= -->
      <g id="screenDashboard">
        <!-- Dashboard Top Header Bar -->
        <rect x="250" y="188" width="300" height="22" rx="5" fill="#ffffff" stroke="#e2e8f0" stroke-width="1" />
        <circle cx="262" cy="199" r="3.5" fill="#f87171" />
        <circle cx="273" cy="199" r="3.5" fill="#fbbf24" />
        <circle cx="284" cy="199" r="3.5" fill="#34d399" />
        <rect x="300" y="195" width="75" height="8" rx="4" fill="#e2e8f0" />
        <rect x="490" y="194" width="50" height="10" rx="5" fill="#e0f2fe" />
        <text x="515" y="202" font-size="7" font-family="sans-serif" font-weight="bold" fill="#0284c7" text-anchor="middle">LIVE MEF</text>

        <!-- Card 1: Top Main Trend Line Chart (Width: 175, Height: 95) -->
        <g transform="translate(250, 216)">
          <rect x="0" y="0" width="180" height="98" rx="6" fill="#ffffff" stroke="#e2e8f0" stroke-width="1" />
          <!-- Header info -->
          <text x="10" y="14" font-size="8" font-family="sans-serif" font-weight="bold" fill="#1e293b">Cambodian Trade Flow</text>
          <text x="10" y="24" font-size="7" font-family="monospace" font-weight="bold" fill="#0284c7">HS 1006.30 · Rice +64%</text>

          <!-- Grid Lines -->
          <line x1="10" y1="40" x2="170" y2="40" stroke="#f1f5f9" stroke-width="1" stroke-dasharray="3,3" />
          <line x1="10" y1="60" x2="170" y2="60" stroke="#f1f5f9" stroke-width="1" stroke-dasharray="3,3" />
          <line x1="10" y1="80" x2="170" y2="80" stroke="#f1f5f9" stroke-width="1" stroke-dasharray="3,3" />

          <!-- Dynamic Filled Gradient Area -->
          <path d="M 12 78 Q 40 45, 65 65 T 115 40 T 168 32 L 168 90 L 12 90 Z" fill="url(#chartSkyGrad)" />
          
          <!-- Secondary Line Chart (Muted Navy) -->
          <path d="M 12 82 Q 40 65, 65 72 T 115 58 T 168 50" stroke="#94a3b8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
          
          <!-- Primary Line Chart (Vibrant Sky Blue) with Pulse -->
          <path d="M 12 78 Q 40 45, 65 65 T 115 40 T 168 32" stroke="#0284c7" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
          
          <!-- Interactive Nodes -->
          <circle cx="12" cy="78" r="3.5" fill="#ffffff" stroke="#0284c7" stroke-width="2" />
          <circle cx="65" cy="65" r="3.5" fill="#ffffff" stroke="#0284c7" stroke-width="2" />
          <circle cx="115" cy="40" r="3.5" fill="#ffffff" stroke="#0284c7" stroke-width="2" />
          <circle cx="168" cy="32" r="5" fill="#38bdf8" stroke="#0369a1" stroke-width="2.5" class="animate-pulse" />
        </g>

        <!-- Card 2: Donut Market Share Chart (Top Right Screen, Width: 110, Height: 98) -->
        <g transform="translate(436, 216)">
          <rect x="0" y="0" width="114" height="98" rx="6" fill="#ffffff" stroke="#e2e8f0" stroke-width="1" />
          <text x="10" y="14" font-size="8" font-family="sans-serif" font-weight="bold" fill="#1e293b">Destinations</text>
          
          <!-- Donut SVG Geometry -->
          <g transform="translate(57, 56)">
            <!-- Outer Ring Backing -->
            <circle cx="0" cy="0" r="28" fill="none" stroke="#f1f5f9" stroke-width="10" />
            <!-- Segment 1: China (Sky Blue 45%) -->
            <circle cx="0" cy="0" r="28" fill="none" stroke="#0284c7" stroke-width="10" stroke-dasharray="78 176" stroke-dashoffset="0" />
            <!-- Segment 2: EU (Cyan 30%) -->
            <circle cx="0" cy="0" r="28" fill="none" stroke="#38bdf8" stroke-width="10" stroke-dasharray="52 176" stroke-dashoffset="-80" />
            <!-- Segment 3: ASEAN (Navy 25%) -->
            <circle cx="0" cy="0" r="28" fill="none" stroke="#082f49" stroke-width="10" stroke-dasharray="44 176" stroke-dashoffset="-134" />
            <text x="0" y="3" font-size="9" font-family="sans-serif" font-weight="bold" fill="#0f172a" text-anchor="middle">EU/CN</text>
          </g>
        </g>

        <!-- Card 3: Bottom Left Bar Metrics (Width: 140, Height: 75) -->
        <g transform="translate(250, 320)">
          <rect x="0" y="0" width="140" height="76" rx="6" fill="#ffffff" stroke="#e2e8f0" stroke-width="1" />
          <text x="10" y="14" font-size="8" font-family="sans-serif" font-weight="bold" fill="#1e293b">Volume ($ USD)</text>

          <!-- Bars -->
          <g transform="translate(14, 24)">
            <!-- Bar 1 -->
            <rect x="0" y="30" width="14" height="18" rx="2" fill="#93c5fd" />
            <!-- Bar 2 -->
            <rect x="22" y="18" width="14" height="30" rx="2" fill="#38bdf8" />
            <!-- Bar 3 -->
            <rect x="44" y="8" width="14" height="40" rx="2" fill="#0284c7" />
            <!-- Bar 4 -->
            <rect x="66" y="2" width="14" height="46" rx="2" fill="#0369a1" />
            <!-- Bar 5 -->
            <rect x="88" y="14" width="14" height="34" rx="2" fill="#38bdf8" />
            <!-- Target Line -->
            <line x1="-5" y1="12" x2="110" y2="12" stroke="#f59e0b" stroke-width="1.5" stroke-dasharray="3,3" />
          </g>
        </g>

        <!-- Card 4: Bottom Right Wave Pulse (Width: 154, Height: 75) -->
        <g transform="translate(396, 320)">
          <rect x="0" y="0" width="154" height="76" rx="6" fill="#ffffff" stroke="#e2e8f0" stroke-width="1" />
          <text x="10" y="14" font-size="8" font-family="sans-serif" font-weight="bold" fill="#1e293b">Realtime FX Sync</text>
          
          <!-- Sinusoidal Waves -->
          <path d="M 12 45 C 30 25, 45 65, 65 40 C 85 15, 105 60, 125 35 C 135 25, 145 40, 148 42" stroke="#38bdf8" stroke-width="2" fill="none" stroke-linecap="round" />
          <path d="M 12 55 C 30 40, 45 70, 65 50 C 85 30, 105 70, 125 45 C 135 35, 145 50, 148 52" stroke="#0284c7" stroke-width="2.5" fill="none" stroke-linecap="round" />
        </g>
      </g>


      <!-- ================= AI ANALYST ROBOT CHARACTER ================= -->
      <g id="aiRobot" class="animate-robot-hover" transform="translate(560, 270)">
        
        <!-- Robot Floating Shadow -->
        <ellipse cx="40" cy="180" rx="35" ry="8" fill="#0f172a" fill-opacity="0.25" class="animate-shadow-pulse" />

        <!-- Robot Body -->
        <g>
          <!-- Antenna -->
          <line x1="40" y1="15" x2="40" y2="35" stroke="#0284c7" stroke-width="4" stroke-linecap="round" />
          <circle cx="40" cy="12" r="7" fill="#38bdf8" stroke="#0369a1" stroke-width="2" class="animate-pulse" />

          <!-- Head Outer Shape -->
          <rect x="10" y="32" width="60" height="46" rx="16" fill="url(#robotBodyGrad)" stroke="#0369a1" stroke-width="3" />
          
          <!-- Head Screen / Visor -->
          <rect x="18" y="40" width="44" height="24" rx="8" fill="#082f49" />
          <!-- Cute Glowing Eyes (Sky Blue Visor) -->
          <g class="animate-robot-blink">
            <ellipse cx="30" cy="52" rx="4.5" ry="5.5" fill="#38bdf8" />
            <ellipse cx="50" cy="52" rx="4.5" ry="5.5" fill="#38bdf8" />
            <circle cx="32" cy="50" r="1.5" fill="#ffffff" />
            <circle cx="52" cy="50" r="1.5" fill="#ffffff" />
          </g>

          <!-- Neck Connector -->
          <rect x="33" y="78" width="14" height="8" rx="2" fill="#082f49" />

          <!-- Main Torso Body -->
          <path d="M 12 92 C 12 84, 20 84, 28 84 L 52 84 C 60 84, 68 84, 68 92 L 72 135 C 72 144, 64 150, 55 150 L 25 150 C 16 150, 8 144, 8 135 Z" fill="url(#robotBodyGrad)" stroke="#0369a1" stroke-width="3" />

          <!-- Torso Chest Screen / Dial -->
          <circle cx="40" cy="116" r="14" fill="#082f49" stroke="#38bdf8" stroke-width="2" />
          <circle cx="40" cy="116" r="6" fill="#34d399" class="animate-pulse" />

          <!-- Left Arm / Hand (Resting) -->
          <path d="M 8 96 Q -6 115, 2 135" stroke="#0284c7" stroke-width="7" stroke-linecap="round" fill="none" />
          <circle cx="2" cy="136" r="6" fill="#38bdf8" stroke="#0369a1" stroke-width="2" />

          <!-- Right Arm (Holding Magnifying Glass & Pointing at Screen) -->
          <g class="animate-robot-arm">
            <!-- Arm Path reaching towards the dashboard -->
            <path d="M 68 96 Q 95 110, 88 130" stroke="#0284c7" stroke-width="7" stroke-linecap="round" fill="none" />
            <circle cx="88" cy="130" r="6" fill="#38bdf8" stroke="#0369a1" stroke-width="2" />

            <!-- Magnifying Glass Tool -->
            <g transform="translate(88, 128) rotate(-25)">
              <line x1="0" y1="0" x2="18" y2="18" stroke="#082f49" stroke-width="4.5" stroke-linecap="round" />
              <circle cx="-10" cy="-10" r="15" fill="#e0f2fe" fill-opacity="0.75" stroke="#0284c7" stroke-width="3.5" />
              <!-- Glass Sparkle -->
              <path d="M -16 -12 Q -12 -16, -6 -16" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round" fill="none" />
              <circle cx="-10" cy="-10" r="3.5" fill="#38bdf8" />
            </g>
          </g>

          <!-- Thruster Propulsion / Hover Base -->
          <path d="M 28 150 L 52 150 L 46 160 L 34 160 Z" fill="#082f49" />
          <!-- Animated Jet Flame -->
          <ellipse cx="40" cy="166" rx="8" ry="6" fill="#38bdf8" class="animate-pulse" />
          <ellipse cx="40" cy="168" rx="4" ry="4" fill="#ffffff" />
        </g>
      </g>

    </svg>
  </div>
</template>

<style scoped>
/* GPU-Accelerated Keyframes for ultra-fast, smooth 60-120fps rendering */
@keyframes floatFast {
  0%, 100% { transform: translate3d(0, 0px, 0); }
  50% { transform: translate3d(0, -6px, 0); }
}

@keyframes floatAlt {
  0%, 100% { transform: translate3d(0, 0px, 0); }
  50% { transform: translate3d(0, 5px, 0); }
}

@keyframes robotHoverFast {
  0%, 100% { transform: translate3d(560px, 270px, 0); }
  50% { transform: translate3d(560px, 262px, 0); }
}

@keyframes robotArmScanFast {
  0%, 100% { transform: rotate(0deg); }
  50% { transform: rotate(-7deg); }
}

@keyframes robotBlink {
  0%, 90%, 100% { transform: scaleY(1); }
  95% { transform: scaleY(0.1); }
}

@keyframes shadowPulseFast {
  0%, 100% { transform: scale(1); opacity: 0.25; }
  50% { transform: scale(0.88); opacity: 0.15; }
}

@keyframes spinFluid {
  from { transform: translate(100px, 110px) rotate(0deg); }
  to { transform: translate(100px, 110px) rotate(360deg); }
}

@keyframes bounceGentle {
  0%, 100% { transform: translate(625px, 465px) translateY(0); }
  50% { transform: translate(625px, 465px) translateY(-5px); }
}

.animate-float-fast {
  animation: floatFast 3s ease-in-out infinite;
  will-change: transform;
}

.animate-float-alt {
  animation: floatAlt 3.5s ease-in-out infinite;
  will-change: transform;
}

.animate-robot-hover {
  animation: robotHoverFast 2.4s ease-in-out infinite;
  will-change: transform;
}

.animate-robot-arm {
  transform-origin: 68px 96px;
  animation: robotArmScanFast 2s ease-in-out infinite;
  will-change: transform;
}

.animate-robot-blink {
  transform-origin: 40px 52px;
  animation: robotBlink 3.2s infinite;
  will-change: transform;
}

.animate-shadow-pulse {
  transform-origin: 40px 180px;
  animation: shadowPulseFast 2.4s ease-in-out infinite;
  will-change: transform, opacity;
}

.animate-spin-fluid {
  transform-origin: 100px 110px;
  animation: spinFluid 16s linear infinite;
  will-change: transform;
}

.animate-bounce-gentle {
  animation: bounceGentle 2.6s ease-in-out infinite;
  will-change: transform;
}
</style>
