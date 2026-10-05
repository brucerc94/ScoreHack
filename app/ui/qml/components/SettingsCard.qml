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
        onAccepted: {
            var path = root.localPath(selectedFile)
            backend.generateTo(path, parseInt(pagesCombo.currentText))
        }
    }

    function localPath(urlValue) {
        var value = String(urlValue)
        if (value.indexOf("file:///") === 0)
            value = value.substring(8)
        return decodeURIComponent(value)
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

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 44
            radius: 9
            color: "#0d1522"
            border.color: "#1b2a3f"

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 8
                spacing: 8

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 1

                    Label {
                        text: "Corregir movimiento"
                        color: "#dbe5f2"
                        font.pixelSize: 12
                        font.bold: true
                    }

                    Label {
                        text: "Sigue desplazamientos de cámara y partitura"
                        color: "#687991"
                        font.pixelSize: 10
                        elide: Text.ElideRight
                    }
                }

                Switch {
                    checked: backend.motionCorrection
                    enabled: !backend.busy
                    onToggled: backend.setMotionCorrection(checked)
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 44
            radius: 9
            color: "#0d1522"
            border.color: "#1b2a3f"

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 8
                spacing: 8

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 1

                    Label {
                        text: "Quitar resaltado móvil"
                        color: "#dbe5f2"
                        font.pixelSize: 12
                        font.bold: true
                    }

                    Label {
                        text: "Elimina la barra/cursor que pasa sobre la partitura"
                        color: "#687991"
                        font.pixelSize: 10
                        elide: Text.ElideRight
                    }
                }

                Switch {
                    checked: backend.removeOverlays
                    enabled: !backend.busy
                    onToggled: backend.setRemoveOverlays(checked)
                }
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

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Button {
                Layout.fillWidth: true
                Layout.preferredHeight: 40
                text: "Vista previa"
                enabled: backend.frameCount > 0 && !backend.busy
                onClicked: backend.preview(parseInt(pagesCombo.currentText))
            }

            Button {
                Layout.fillWidth: true
                Layout.preferredHeight: 40
                text: "Generar PDF"
                enabled: backend.frameCount > 0 && !backend.busy
                onClicked: pdfDialog.open()
            }
        }
    }
}
