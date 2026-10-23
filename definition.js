// MH-Z19B CO2 sensor - OhStem App (Yolo:Bit) extension
// Python library: mhz19b.py (based on overflo23/MH-Z19_MicroPython, MIT)

var MHZ19B_COLOUR = "#1f9d8a";

function mhz19b_imports() {
  Blockly.Python.definitions_["import_yolobit"] = "from yolobit import *";
  Blockly.Python.definitions_["import_mhz19b"] = "from mhz19b import *";
}

// ---------------------------------------------------------------------------
// Khởi tạo
// ---------------------------------------------------------------------------
Blockly.Blocks["mhz19b_init"] = {
  init: function () {
    this.jsonInit({
      colour: MHZ19B_COLOUR,
      nextStatement: null,
      previousStatement: null,
      message0: "khởi tạo cảm biến CO2 MH-Z19B  TX %1  RX %2",
      args0: [
        { type: "field_dropdown", name: "TX", options: digitalPins },
        { type: "field_dropdown", name: "RX", options: digitalPins }
      ],
      tooltip:
        "TX và RX là chân của Yolo:Bit. Chân TX của Yolo:Bit nối vào RX của cảm biến, " +
        "chân RX của Yolo:Bit nối vào TX của cảm biến. Cảm biến cấp nguồn 5V. " +
        "Nếu đọc ra -1, hãy thử đổi chỗ TX và RX.",
      helpUrl: ""
    });
    // cảnh báo khi chọn trùng chân
    this.setOnChange(function () {
      if (!this.workspace || this.isInFlyout) return;
      if (this.getFieldValue("TX") === this.getFieldValue("RX")) {
        this.setWarningText("TX và RX đang chọn cùng một chân");
      } else {
        this.setWarningText(null);
      }
    });
  }
};

Blockly.Python["mhz19b_init"] = function (block) {
  mhz19b_imports();
  var tx = block.getFieldValue("TX");
  var rx = block.getFieldValue("RX");
  return "mhz19b_init(" + tx + ", " + rx + ")\n";
};

// ---------------------------------------------------------------------------
// Đọc dữ liệu
// ---------------------------------------------------------------------------
Blockly.Blocks["mhz19b_read_co2"] = {
  init: function () {
    this.jsonInit({
      colour: MHZ19B_COLOUR,
      output: "Number",
      message0: "nồng độ CO2 MH-Z19B (ppm)",
      args0: [],
      tooltip:
        "Đọc nồng độ CO2 trong không khí (ppm). Trả về -1 nếu cảm biến không phản hồi. " +
        "Cảm biến cần khoảng 3 phút làm nóng sau khi cấp nguồn.",
      helpUrl: ""
    });
  }
};

Blockly.Python["mhz19b_read_co2"] = function (block) {
  mhz19b_imports();
  return ["mhz19b_co2()", Blockly.Python.ORDER_ATOMIC];
};

Blockly.Blocks["mhz19b_read_temp"] = {
  init: function () {
    this.jsonInit({
      colour: MHZ19B_COLOUR,
      output: "Number",
      message0: "nhiệt độ cảm biến MH-Z19B (°C)",
      args0: [],
      tooltip:
        "Nhiệt độ đo bởi MH-Z19B (độ chính xác thấp, chỉ mang tính tham khảo). " +
        "Trả về -99 nếu cảm biến không phản hồi.",
      helpUrl: ""
    });
  }
};

Blockly.Python["mhz19b_read_temp"] = function (block) {
  mhz19b_imports();
  return ["mhz19b_temp()", Blockly.Python.ORDER_ATOMIC];
};

Blockly.Blocks["mhz19b_is_ready"] = {
  init: function () {
    this.jsonInit({
      colour: MHZ19B_COLOUR,
      output: "Boolean",
      message0: "MH-Z19B đã làm nóng xong (3 phút)",
      args0: [],
      tooltip: "Đúng khi đã qua 3 phút kể từ lúc khởi tạo cảm biến. Trước đó số đo chưa ổn định.",
      helpUrl: ""
    });
  }
};

Blockly.Python["mhz19b_is_ready"] = function (block) {
  mhz19b_imports();
  return ["mhz19b_ready()", Blockly.Python.ORDER_ATOMIC];
};

// ---------------------------------------------------------------------------
// Hiệu chuẩn / cài đặt
// ---------------------------------------------------------------------------
Blockly.Blocks["mhz19b_calibrate_zero"] = {
  init: function () {
    this.jsonInit({
      colour: MHZ19B_COLOUR,
      nextStatement: null,
      previousStatement: null,
      message0: "hiệu chuẩn điểm 0 (400 ppm) cho MH-Z19B",
      args0: [],
      tooltip:
        "Đặt cảm biến ngoài trời thoáng khí khoảng 20 phút rồi mới dùng khối này. " +
        "Khối này chỉ cần chạy một lần, không đặt trong vòng lặp.",
      helpUrl: ""
    });
  }
};

Blockly.Python["mhz19b_calibrate_zero"] = function (block) {
  mhz19b_imports();
  return "mhz19b_calibrate_zero()\n";
};

Blockly.Blocks["mhz19b_auto_calibrate"] = {
  init: function () {
    this.jsonInit({
      colour: MHZ19B_COLOUR,
      nextStatement: null,
      previousStatement: null,
      message0: "%1 tự hiệu chuẩn (ABC) của MH-Z19B",
      args0: [
        {
          type: "field_dropdown",
          name: "ON",
          options: [["bật", "True"], ["tắt", "False"]]
        }
      ],
      tooltip:
        "Tự hiệu chuẩn điểm 0 mỗi 24 giờ, giả định mỗi ngày không khí có lúc xuống ~400 ppm. " +
        "Nên tắt nếu đặt cảm biến ở nơi luôn có người (phòng kín, lớp học...).",
      helpUrl: ""
    });
  }
};

Blockly.Python["mhz19b_auto_calibrate"] = function (block) {
  mhz19b_imports();
  var on = block.getFieldValue("ON");
  return "mhz19b_auto_calibrate(" + on + ")\n";
};

Blockly.Blocks["mhz19b_set_range"] = {
  init: function () {
    this.jsonInit({
      colour: MHZ19B_COLOUR,
      nextStatement: null,
      previousStatement: null,
      message0: "đặt dải đo MH-Z19B là %1 ppm",
      args0: [
        {
          type: "field_dropdown",
          name: "RANGE",
          options: [["2000", "2000"], ["5000", "5000"]]
        }
      ],
      tooltip: "Chọn dải đo tối đa. Dải 2000 ppm chính xác hơn ở nồng độ thấp.",
      helpUrl: ""
    });
  }
};

Blockly.Python["mhz19b_set_range"] = function (block) {
  mhz19b_imports();
  var range = block.getFieldValue("RANGE");
  return "mhz19b_set_range(" + range + ")\n";
};