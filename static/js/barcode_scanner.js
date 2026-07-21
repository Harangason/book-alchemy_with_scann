const isbnInput = document.getElementById("isbn");
const startButton = document.getElementById("start-scanner");
const stopButton = document.getElementById("stop-scanner");
const statusText = document.getElementById("scanner-status");
const video = document.getElementById("barcode-preview");

let scannerStream = null;
let scannerActive = false;

function setScannerStatus(message) {
    statusText.textContent = message;
}

function normalizeIsbn(value) {
    return value.replace(/[^0-9X]/gi, "");
}

function stopScanner() {
    scannerActive = false;

    if (scannerStream) {
        scannerStream.getTracks().forEach((track) => track.stop());
        scannerStream = null;
    }

    video.hidden = true;
    stopButton.hidden = true;
    startButton.hidden = false;
}

async function scanFrame(detector) {
    if (!scannerActive) {
        return;
    }

    try {
        const barcodes = await detector.detect(video);
        const barcode = barcodes.find((item) => {
            const rawValue = normalizeIsbn(item.rawValue);
            return rawValue.length === 10 || rawValue.length === 13;
        });

        if (barcode) {
            isbnInput.value = normalizeIsbn(barcode.rawValue);
            setScannerStatus(`ISBN erkannt: ${isbnInput.value}`);
            stopScanner();
            return;
        }
    } catch (error) {
        setScannerStatus("Barcode konnte in diesem Frame nicht gelesen werden.");
    }

    window.requestAnimationFrame(() => scanFrame(detector));
}

async function startScanner() {
    if (!("BarcodeDetector" in window)) {
        setScannerStatus("Dieser Browser unterstützt Barcode-Scanning nicht. Nutze Chrome/Edge auf Android oder gib die ISBN manuell ein.");
        return;
    }

    try {
        const detector = new BarcodeDetector({
            formats: ["ean_13", "ean_8", "upc_a", "upc_e", "code_128"],
        });

        scannerStream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: "environment" },
            audio: false,
        });

        video.srcObject = scannerStream;
        video.hidden = false;
        startButton.hidden = true;
        stopButton.hidden = false;
        scannerActive = true;
        setScannerStatus("Scanner läuft. Richte die Kamera auf den ISBN-Barcode.");

        await video.play();
        scanFrame(detector);
    } catch (error) {
        stopScanner();
        setScannerStatus("Kamera konnte nicht gestartet werden. Prüfe Browser-Berechtigung und HTTPS/localhost.");
    }
}

startButton.addEventListener("click", startScanner);
stopButton.addEventListener("click", () => {
    stopScanner();
    setScannerStatus("Scanner gestoppt.");
});
