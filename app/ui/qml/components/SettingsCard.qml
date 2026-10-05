import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

Rectangle {
    id: root
    Layout.preferredWidth: 315
    Layout.fillHeight: true
    radius: 16
    color: "#111827"
    border.color: "#1d2a3c"
    clip: true

    FileDialog {
        id: pdfDialog
        title: "Guardar PDF"
        nameFilters: ["PDF (*.pdf)"]
        fileMode: FileDialog.SaveFile
        currentFile: "partitura.pdf"

        onAccepted: {
            backend.generateTo(
                selectedFile.toLocalFile(),
                parseInt(pagesCombo.currentText)
            )
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 6

        Label {
            text: "Ajustes"
            color: "#f4f7fb"
            font.pixelSize: 16
            font.bold: true
        }

        Label {
            text: "Intervalo entre frames (s)"
            color: "#8290a6"
            font.pixelSize: 12
        }

        TextField {
            id: intervalField
            Layout.fillWidth: true
            Layout.preferredHeight: 34
            text: "1.0"
            selectByMouse: true
            validator: DoubleValidator { bottom: 0.1; top: 60.0; decimals: 2 }
            onEditingFinished: backend.setInterval(Number(text))
            color: "#e8edf5"
            font.pixelSize: 12
            background: Rectangle {
                radius: 8
                color: "#0d1522"
                border.color: "#263752"
            }
        }

        Label {
            text: "Recorte superior"
            color: "#8290a6"
            font.pixelSize: 12
            Layout.topMargin: 5
        }

        Slider {
            Layout.fillWidth: true
            Layout.preferredHeight: 24
            from: 0
            to: Math.max(1, backend.videoHeight - 2)
            value: backend.cropTop
            enabled: backend.frameCount > 0
            onMoved: backend.setCropTop(value)
        }

        Label {
            text: backend.cropTop + " px"
            color: "#667891"
            font.pixelSize: 11
        }

        Label {
            text: "Recorte inferior"
            color: "#8290a6"
            font.pixelSize: 12
            Layout.topMargin: 4
        }

        Slider {
            Layout.fillWidth: true
            Layout.preferredHeight: 24
            from: 0
            to: Math.max(1, backend.videoHeight - 2)
            value: backend.cropBottom
            enabled: backend.frameCount > 0
            onMoved: backend.setCropBottom(value)
        }

        Label {
            text: backend.cropBottom + " px"
            color: "#667891"
            font.pixelSize: 11
        }

        Label {
            text: "Rango de frames"
            color: "#8290a6"
            font.pixelSize: 12
            Layout.topMargin: 5
        }

        Label {
            text: (backend.rangeStart + 1) + " → " + (backend.rangeEnd + 1)
            color: "#cbd5e3"
            font.pixelSize: 12
            font.bold: true
        }

        Slider {
            Layout.fillWidth: true
            Layout.preferredHeight: 24
            from: 0
            to: Math.max(1, backend.frameCount - 1)
            value: backend.rangeStart
            enabled: backend.frameCount > 0
            onMoved: backend.setRangeStart(value)
        }

        Slider {
            Layout.fillWidth: true
            Layout.preferredHeight: 24
            from: 0
            to: Math.max(1, backend.frameCount - 1)
            value: backend.rangeEnd
            enabled: backend.frameCount > 0
            onMoved: backend.setRangeEnd(value)
        }

        Label {
            text: "Partituras por página"
            color: "#8290a6"
            font.pixelSize: 12
            Layout.topMargin: 5
        }

        ComboBox {
            id: pagesCombo
            Layout.fillWidth: true
            Layout.preferredHeight: 34
            model: ["1", "2", "3", "4", "5", "6", "7", "8"]
            currentIndex: 3
        }

        Item { Layout.fillHeight: true }

        Button {
            Layout.fillWidth: true
            Layout.preferredHeight: 40
            text: "Generar PDF"
            enabled: backend.frameCount > 0 && !backend.busy
            onClicked: pdfDialog.open()
        }
    }
}
