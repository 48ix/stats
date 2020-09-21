<div align="center">
  
  <img src="https://res.cloudinary.com/ix-48/image/upload/v1594108320/logo-wide-light.svg" />

  <br/>
  <div style="color: #808080; font-style:italic;">
    <h3>
      STATS
    </h3>
  </div>

</div>

<hr/>

This repository contains the REST API and stats collection code for [48 IX](https://48ix.net).

## How it Works

48 IX utilizes [InfluxDB]([https://](https://www.influxdata.com/products/influxdb-overview/)) & [Telegraf](https://www.influxdata.com/time-series-platform/telegraf/) to collect and store telemetry from our infrastructure. The stats API provides an easier way to consume that data both for automated purposes and [our website](https://48ix.net).
