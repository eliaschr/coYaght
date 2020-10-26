var Logo;

var LogoOpacityMin = 0;
var LogoOpacityMax = 1;
var LogoFadeNow = 0;
var LogoFadeTime = 1000;
var LogoStep = 20;
var LogoOpacity = 0;

var LogoStartX;
var LogoStartY;
var LogoStartH;
var LogoX;
var LogoY;
var LogoH;
var LogoEndX = 0;
var LogoEndY = 0;
var LogoEndH;
var LogoPosNow = 0;
var LogoPosTime = 1000;
var LogoPosStep = 20;

var RTCTElem;
var RTCDElem;
var MainElem;

var xmlReq = new XMLHttpRequest();
var xmlStartReq = new XMLHttpRequest();
var xmlStopReq = new XMLHttpRequest();
var CurRTCTime;
var RTCJson;
var RTCDiffTime;

var buttons;
var lastreq = null;
var xmlReqOK = true;
var xmlResume = null;
var xmlStartOK = true;
var xmlStartResume = null;
var xmlStopOK = true;
var xmlStopResume = null;

var KeyGroupV = new Map();
var KeyGroupH = new Map();
var lastVKey;
var lastHKey;

var RadioElems;
var PVal;
var PLabels = [
	["Pressure (KPa)", 1, -1],
	["Depth (m)", -1, 20]
]
var PBuffer = new Array();

var PTElem;
var PTChart;
var PTOpts;
var PTData;
var LVElem;
var LVChart;
var LVOpts;
var LVData;

var dataStat = false;
var vidElem;

function startConnect() {
	var LogoPos;
	var Hr;

	KeyGroupV.set("KeyQ", "btn-up");
	KeyGroupV.set("KeyA", "btn-dn");

	KeyGroupH.set("Numpad1", "btn-tbl");
	KeyGroupH.set("Numpad2", "btn-bk");
	KeyGroupH.set("Numpad3", "btn-tbr");
	KeyGroupH.set("Numpad4", "btn-rccw");
	KeyGroupH.set("Numpad6", "btn-rcw");
	KeyGroupH.set("Numpad7", "btn-tfl");
	KeyGroupH.set("Numpad8", "btn-fr");
	KeyGroupH.set("Numpad9", "btn-tfr");

	Logo = document.getElementById("DSRLogo");
	Logo.style.position = "absolute";

	Hr = document.getElementById("HRSep");
	Hr.style.position = "absolute";
	LogoEndH = Hr.getBoundingClientRect().top +1;
	Hr.style.position = "relative";

	LogoPos = Logo.getBoundingClientRect();
	LogoStartX = LogoPos.x;
	LogoStartY = LogoPos.y;
	LogoStartH = LogoPos.height;

	buttons = document.getElementsByClassName("btn");
	for(var i = 0; i < buttons.length; i++) {
		var elem = buttons[i];
		elem.ondragstart = stopDrag;
	}

	RTCDElem = document.getElementById("RTCDate");
	RTCTElem = document.getElementById("RTCTime");
	MainElem = document.getElementById("mainTbl");
	vidElem = document.getElementById("imgVideo");

	initRadios();

	initPTGraph();
	initLVGraph();

	setTimeout("FadeInLogo(" + new Date().getTime() + ")", LogoStep);
}

function initRadios() {
	RadioElems = document.getElementsByName("PVal");
	for(var i = 0; i < RadioElems.length; i++) {
		RadioElems[i].onchange = PValChanged;
		if(RadioElems[i].checked) {
			PVal = RadioElems[i].value;
		}
	}
}

function initPTGraph() {
	PTElem = document.getElementById("ChartPT");

	PTData = new google.visualization.DataTable();
	PTData.addColumn('datetime', 'Time');
	PTData.addColumn('number', PLabels[PVal][0]);
	PTData.addColumn('number', 'Temperature (C)');

	PTOpts = {
		title: 'coYaght Pressure and Temperature Sensors',
		curveType: 'function',
		series: {
			0: {targetAxisIndex: 0},
			1: {targetAxisIndex: 1}
		},
		vAxes: {
			0: {title: PLabels[PVal][0],
				direction: PLabels[PVal][1],
				minValue: 0,
				maxValue: PLabels[PVal][2],
				textStyle: {
					color: 'blue'
					}
				},
			1: {title: 'Temperature (C)',
				minValue: -19,
				maxValue: 49,
				textStyle: {
					color: 'green'
					}
				}
		},
		hAxis: {
			textPosition: "none",
			textStyle: {
				fontSize: 0
			}
		},
		legend: { position: 'bottom' },
		colors: ['blue', 'green']
	};

	PTChart = new google.visualization.LineChart(PTElem);
}

function initLVGraph() {
	LVElem = document.getElementById("ChartLV");

	LVData = new google.visualization.DataTable();
	LVData.addColumn('datetime', 'Time');
	LVData.addColumn('number', 'Light (Lux)');
	LVData.addColumn('number', 'Power Supply (V)');

	LVOpts = {
		title: 'coYaght Light Sensor and Battery Voltage',
		curveType: 'function',
		series: {
			0: {targetAxisIndex: 0},
			1: {targetAxisIndex: 1}
		},
		vAxes: {
			0: {title: 'Lux',
				minValue: 0,
				textStyle: {
					color: '#C0C000'
					}
				},
			1: {title: 'Volts',
				minValue: 0,
				maxValue: 15,
				textStyle: {
					color: 'red'
					}
				}
		},
		hAxis: {
			textPosition: "none",
			textStyle: {
				fontSize: 0
			},
			//format: 'yyyy-MM-dd HH:mm:ss'
		},
		legend: { position: 'bottom' },
		colors: ['#C0C000', 'red']
	};

	LVChart = new google.visualization.LineChart(LVElem);
}

function stopDrag() {
	return false;
}

function imgPressed(elemId) {
	if((lastreq) && (lastreq != elemId)) {
		document.getElementById(lastreq).className = "btn";
	}
	lastreq = elemId;
	xmlResume = imgPResume;
	imgClicked(elemId);
}

function imgPrKey(elemId) {
	imgClicked(elemId);
}

function imgPResume() {
	xmlResume = null;
	if(lastreq) {
		document.getElementById(lastreq).className = "btnsel";
	}
}

function imgDepressed(elemId) {
	if(lastreq) {
		xmlResume = imgDResume;
		sendReq(lastreq, "off");
	}
	lastreq = null;
}

function imgDeprKey(elemId) {
	xmlResume = imgCResume;
	sendReq(elemId, "off");
}

function imgDResume() {
	if(lastreq) {
		document.getElementById(lastreq).className = "btn";
	}
	xmlResume = null;
}

function imgClicked(elemId) {
	if(!xmlResume) {
		xmlResume = imgCResume;
	}
	sendReq(elemId, "on");
}

function videoClicked() {
	videoStat = document.getElementById('btn-vdst').hidden;
	if(videoStat) {
		xmlResume = videoResume;
		sendReq('btn-vsp', 'on');
	} else {
		videoResume();
	}
}

function videoResume() {
	videoStat = document.getElementById('btn-vdst').hidden;
	if(videoStat) {
		vidElem.src = 'stream.jpg?t=' + new Date().getTime();
	} else {
		vidElem.src = 'stream.mjpg?t=' + new Date().getTime();
	}
	document.getElementById('btn-vdst').hidden = !videoStat;
	document.getElementById('btn-vdsp').hidden = videoStat;
	xmlResume = null;
}

function dataStart() {
	if(dataStat) {
		return;
	}
	dataStat = true;
	xmlStartResume = dataStartResume;
	sendStart();
}

function sendStart() {
	xmlStartOK = false;
	xmlStartReq.open('POST', '/btn-dst', true);
	xmlStartReq.setRequestHeader("Content-Type","text/plain");
	//xmlStartReq.setRequestHeader("Content-Length", 0);
	//xmlStartReq.setRequestHeader("Connection", "keep-alive");
	xmlStartReq.onreadystatechange = xmlStartResume;
	xmlStartReq.send('on');
}

function dataStartResume() {
	if(xmlStartReq.readyState == 4 && xmlStartReq.status == 200) {
		document.getElementById('btn-dst').hidden = true;
		document.getElementById('btn-dsp').hidden = false;
		xmlStartOK = true;
		RowsNum = PTData.getNumberOfRows();
		PTData.removeRows(0, RowsNum);
		LVData.removeRows(0, RowsNum);
		PBuffer.length = 0;
		inData = JSON.parse(xmlStartReq.responseText);
		reDrawPTGraph(inData);
		reDrawLVGraph(inData);
		if(dataStat) {
			xmlStartResume = dataStartCont;
			sendStart();
		}
	}
}

function dataStartCont() {
	if(xmlStartReq.readyState == 4 && xmlStartReq.status == 200) {
		xmlStartOK = true;
		inData = JSON.parse(xmlStartReq.responseText);
		reDrawPTGraph(inData);
		reDrawLVGraph(inData);
		if(dataStat) {
			sendStart();
		}
	}
}

function reDrawPTGraph(inData) {
	var ShowVal = PVal == 0 ? inData.pressure : inData.depth;
	var BuffVal = PVal == 0 ? inData.depth : inData.pressure;
	PTData.addRow([
		new Date(inData.datestamp),
		ShowVal,
		inData.temp
	]);
	PBuffer.push(BuffVal);
	PTChart.draw(PTData, PTOpts);
}

function reDrawLVGraph(inData) {
	LVData.addRow([
		new Date(inData.datestamp),
		inData.lux,
		inData.battery
	]);
	LVChart.draw(LVData, LVOpts);
}

function dataStop() {
	if(!dataStat) {
		return;
	}
	dataStat = false;
	sendStop();
}

function sendStop() {
	xmlStopOK = false;
	xmlStopReq.open('POST', '/btn-dsp', true);
	xmlStopReq.setRequestHeader("Content-Type","text/plain");
	//xmlStopReq.setRequestHeader("Content-Length", 0);
	//xmlStopReq.setRequestHeader("Connection", "keep-alive");
	xmlStopReq.onreadystatechange = dataStopResume;
	xmlStopReq.send('on');
}

function dataStopResume() {
	if(xmlStopReq.readyState == 4 && xmlStopReq.status == 200) {
		document.getElementById('btn-dst').hidden = false;
		document.getElementById('btn-dsp').hidden = true;
		xmlStopOK = true;
	}
}

function PValChanged() {
	for(var i = 0; i < RadioElems.length; i++) {
		if(RadioElems[i].checked) {
			PVal = RadioElems[i].value;
		}
	}
	PTOpts.vAxes[0].title = PLabels[PVal][0];
	PTOpts.vAxes[0].direction = PLabels[PVal][1];
	PTOpts.vAxes[0].maxValue = PLabels[PVal][2];
	PTData.setColumnLabel = PLabels[PVal][0];

	var TempVal;
	for(var i = 0; i < PBuffer.length; i++) {
		TempVal = PBuffer[i];
		PBuffer[i] = PTData.getValue(i, 1);
		PTData.setValue(i, 1, TempVal);
	}
	PTChart.draw(PTData, PTOpts);
}

function imgCResume() {
	xmlResume = null;
}

function keyPressed(e) {
	if(e.repeat) {
		return;
	}
	key = e.code;
	if(KeyGroupV.has(key)) {
		lastVKey = key;
		val = KeyGroupV.get(key);
		imgPrKey(val);
		document.getElementById(val).className = "btnsel";
	} else if (KeyGroupH.has(key)) {
		lastHKey = key;
		val = KeyGroupH.get(key);
		imgPrKey(val);
		document.getElementById(val).className = "btnsel";
	}
}

function keyDepressed(e) {
	key = e.code;
	if(KeyGroupV.has(key)) {
		val = KeyGroupV.get(key);
		document.getElementById(val).className = "btn";
		if(lastVKey == key) {
			imgDeprKey(val);
			lastVKey = null;
		}
	} else if(KeyGroupH.has(key)) {
		val = KeyGroupH.get(key);
		document.getElementById(val).className = "btn";
		if(lastHKey == key) {
			imgDeprKey(val);
			lastHKey = null;
		}
	}
}

function sendReq(elem, st) {
	xmlReqOK = false;
	xmlReq.open('POST', '/' + elem, true);
	xmlReq.setRequestHeader("Content-Type","text/plain");
	//xmlReq.setRequestHeader("Content-Length", 0);
	//xmlReq.setRequestHeader("Connection", "keep-alive");
	xmlReq.onreadystatechange = sendReqState;
	xmlReq.send(st);
}

function sendReqState() {
	if(xmlReq.readyState == 4) {
		xmlReqOK = true;
	}
	if(xmlResume) {
		xmlResume();
	}
}

function FadeInLogo(timeval) {
	var CurTime = new Date().getTime();
	var Interval = CurTime - timeval;

	LogoFadeNow += Interval;
	if(LogoFadeNow >= LogoFadeTime) {
		Logo.style.opacity = LogoOpacityMax;
		Logo.style.filter = "alpha(opacity=" + (LogoOpacityMax *100) + ")";
		waitInit();
		return;
	}
	LogoOpacity = LogoOpacityMax*LogoFadeNow/LogoFadeTime + LogoOpacityMin;
	Logo.style.opacity = LogoOpacity;
	Logo.style.filter = "alpha(opacity = " + (LogoOpacity * 100) + ")";

	setTimeout("FadeInLogo(" + CurTime + ")", LogoStep);
}

function waitInit() {
	xmlReq.open('POST', '/waitInit', true);
	xmlReq.setRequestHeader("Content-Type","text/plain");
	//xmlReq.setRequestHeader("Content-Length", 0);
	//xmlReq.setRequestHeader("Connection", "keep-alive");
	xmlReq.onreadystatechange = waitInitState;
	xmlReq.send(null);
}

function waitInitState() {
	if(xmlReq.readyState == 4 && xmlReq.status == 200) {
		setTimeout("PositionLogo(" + new Date().getTime() + ")", LogoPosStep);
		var te = document.getElementById("SenStat");
		te.innerHTML = "Connected";
		te.style.color = "#009020";
	}
}

function PositionLogo(timeval) {
	var CurTime = new Date().getTime();
	var Interval = CurTime - timeval;

	LogoPosNow += Interval;
	if(LogoPosNow >= LogoPosTime) {
		Logo.style.left = LogoEndX + "px";
		Logo.style.top = LogoEndY + "px";
		Logo.style.height = LogoEndH + "px";
		getRTCReq();
		return;
	}
	LogoX = LogoStartX - (LogoStartX - LogoEndX)*LogoPosNow/LogoPosTime;
	LogoY = LogoStartY - (LogoStartY - LogoEndY)*LogoPosNow/LogoPosTime;
	LogoH = LogoStartH - (LogoStartH - LogoEndH)*LogoPosNow/LogoPosTime;
	Logo.style.left = LogoX + "px";
	Logo.style.top = LogoY + "px";
	Logo.style.height = LogoH + "px";

	setTimeout("PositionLogo(" + CurTime + ")", LogoPosStep);

}

function getRTCReq() {
	xmlReq.open('POST', '/getRTC', true);
	xmlReq.setRequestHeader("Content-Type","text/plain");
	//xmlReq.setRequestHeader("Content-Length", 0);
	//xmlReq.setRequestHeader("Connection", "keep-alive");
	xmlReq.onreadystatechange = getRTCState;
	xmlReq.send(null);
}

function getRTCState() {
	if(xmlReq.readyState == 4 && xmlReq.status == 200) {
		CurRTCTime = new Date();
		RTCJson = JSON.parse(xmlReq.responseText);
		RTCDiffTime = CurRTCTime.getTime() - RTCJson.epoch *1000;
		setTimeout("setRTCVal()", 1000);
		MainElem.style.display = "table";
		MainElem.style.opacity = 1;
		MainElem.style.filter = "alpha(opacity=100)";
		document.onkeydown = keyPressed;
		document.onkeyup = keyDepressed;
		initDrawCharts();
	}
}

function initDrawCharts() {
	PTData.addRow(
		[new Date(), 0, 0]
		   );
	PBuffer.push(0);
	PTChart.draw(PTData, PTOpts);

	LVData.addRow(
		[new Date(), 0, 0]
	);
	LVChart.draw(LVData, LVOpts);
}

function setRTCVal() {
	var tt = new Date().getTime();
	tt -= RTCDiffTime;

	var td = new Date(tt);
	var day = td.getDate();
	if(day <10) {
		day = "0" + day;
	}
	var mon = td.getMonth() +1;
	if(mon <10) {
		mon = "0" + mon;
	}
	var year = td.getFullYear();
	RTCDElem.innerHTML = day + "/" + mon + "/" + year;

	var hour = td.getHours();
	if(hour <10) {
		hour = "0" + hour;
	}
	var mins = td.getMinutes();
	if(mins <10) {
		mins = "0" + mins;
	}
	var secs = td.getSeconds();
	if(secs <10) {
		secs = "0" + secs;
	}
	RTCTElem.innerHTML = hour + ":" + mins + ":" + secs;

	setTimeout("setRTCVal()", 1000);
}
