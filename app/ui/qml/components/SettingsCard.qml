import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

Rectangle {
    id: root
    Layout.preferredWidth: 350
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
        anchors.margins: 18
        spacing: 10

        RowLayout {
            Layout.fillWidth: true
            Label {
                text: "Ajustes"
                color: "#f4f7fb"
                font.pixelSize: 18
                font.bold: true
            }
            Item { Layout.fillWidth: true }
            Label {
                text: backend.layoutMode === "horizontal" ? "RECONSTRUCCIÓN" : "INDIVIDUAL"
                color: "#6f86a5"
                font.pixelSize: 9
                font.bold: true
            }
        }

        Label {
            text: "Recorte"
            color: "#a9b6c9"
            font.pixelSize: 12
            font.bold: true
            Layout.topMargin: 2
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 132
            radius: 10
            color: "#0d1522"
            border.color: "#1b2a3f"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 6

                Label {
                    text: "Zona útil de la partitura"
                    color: "#dbe5f2"
                    font.pixelSize: 11
                    font.bold: true
                }

                Label {
                    text: "Superior: " + backend.cropTop + " px"
                    color: "#70819a"
                    font.pixelSize: 10
                }

                Slider {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 24
                    from: 0
                    to: Math.max(1, backend.videoHeight - backend.cropBottom - 2)
                    value: backend.cropTop
                    enabled: backend.frameCount > 0
                    onMoved: backend.setCropTop(value)
                }

                Label {
                    text: "Inferior: " + backend.cropBottom + " px"
                    color: "#70819a"
                    font.pixelSize: 10
                }

                Slider {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 24
                    from: 0
                    to: Math.max(1, backend.videoHeight - backend.cropTop - 2)
                    value: backend.cropBottom
                    enabled: backend.frameCount > 0
                    onMoved: backend.setCropBottom(value)
                }
            }
        }

        ScrollView {
            id: settingsScroll
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            ScrollBar.vertical.policy: ScrollBar.AsNeeded
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

            ColumnLayout {
                width: settingsScroll.availableWidth
                spacing: 9

                Label {
                    text: "Captura"
                    color: "#a9b6c9"
                    font.pixelSize: 12
                    font.bold: true
                    Layout.topMargin: 2
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 72
                    radius: 10
                    color: "#0d1522"
                    border.color: "#1b2a3f"

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 5

                        Label {
                            text: "Intervalo entre frames"
                            color: "#dbe5f2"
                            font.pixelSize: 12
                            font.bold: true
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            TextField {
                                id: intervalField
                                Layout.fillWidth: true
                                Layout.preferredHeight: 34
                                text: "1.0"
                                validator: DoubleValidator { bottom: 0.1; top: 60.0; decimals: 2 }
                                onEditingFinished: backend.setInterval(Number(text))
                                color: "#e8edf5"
                                font.pixelSize: 12
                                background: Rectangle {
                                    radius: 8
                                    color: "#111a28"
                                    border.color: "#263752"
                                }
                            }
                            Label { text: "seg"; color: "#71829a"; font.pixelSize: 11 }
                        }
                    }
                }

                Label {
                    text: "Preparación de imagen"
                    color: "#a9b6c9"
                    font.pixelSize: 12
                    font.bold: true
                    Layout.topMargin: 3
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 64
                    radius: 10
                    color: "#0d1522"
                    border.color: "#1b2a3f"

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 8

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            Label {
                                text: "Corregir movimiento"
                                color: "#dbe5f2"
                                font.pixelSize: 12
                                font.bold: true
                            }
                            Label {
                                text: backend.layoutMode === "horizontal"
                                      ? "Se desactiva en reconstrucción"
                                      : "Alinea pequeños desplazamientos"
                                color: "#687991"
                                font.pixelSize: 10
                            }
                        }
                        Switch {
                            checked: backend.motionCorrection
                            enabled: !backend.busy && backend.layoutMode === "individual"
                            onToggled: backend.setMotionCorrection(checked)
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 64
                    radius: 10
                    color: "#0d1522"
                    border.color: "#1b2a3f"

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 8

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            Label {
                                text: "Quitar resaltado móvil"
                                color: "#dbe5f2"
                                font.pixelSize: 12
                                font.bold: true
                            }
                            Label {
                                text: "Elimina cursor o barra coloreada"
                                color: "#687991"
                                font.pixelSize: 10
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
                    text: "Salida"
                    color: "#a9b6c9"
                    font.pixelSize: 12
                    font.bold: true
                    Layout.topMargin: 3
                }

                Label {
                    text: "Modo"
                    color: "#687991"
                    font.pixelSize: 10
                }

                ComboBox {
                    id: layoutCombo
                    Layout.fillWidth: true
                    Layout.preferredHeight: 38
                    model: ["Individual", "Unión horizontal"]
                    currentIndex: backend.layoutMode === "horizontal" ? 1 : 0
                    enabled: !backend.busy
                    onActivated: backend.setLayoutMode(currentIndex === 1 ? "horizontal" : "individual")
                }

                ColumnLayout {
                    visible: backend.layoutMode === "individual"
                    Layout.fillWidth: true
                    spacing: 7

                    Label {
                        text: "Rango de frames"
                        color: "#687991"
                        font.pixelSize: 10
                    }

                    Label {
                        text: (backend.rangeStart + 1) + "  →  " + (backend.rangeEnd + 1)
                        color: "#dbe5f2"
                        font.pixelSize: 12
                        font.bold: true
                    }

                    Slider {
                        Layout.fillWidth: true
                        from: 0
                        to: Math.max(1, backend.frameCount - 1)
                        value: backend.rangeStart
                        enabled: backend.frameCount > 0
                        onMoved: backend.setRangeStart(value)
                    }

                    Slider {
                        Layout.fillWidth: true
                        from: 0
                        to: Math.max(1, backend.frameCount - 1)
                        value: backend.rangeEnd
                        enabled: backend.frameCount > 0
                        onMoved: backend.setRangeEnd(value)
                    }

                    Label {
                        text: "Partituras por página"
                        color: "#687991"
                        font.pixelSize: 10
                        Layout.topMargin: 2
                    }

                    ComboBox {
                        id: pagesCombo
                        Layout.fillWidth: true
                        Layout.preferredHeight: 38
                        model: ["1", "2", "3", "4", "5", "6", "7", "8"]
                        currentIndex: 3
                    }
                }

                ColumnLayout {
                    visible: backend.layoutMode === "horizontal"
                    Layout.fillWidth: true
                    spacing: 8

                    Label {
                        text: "Distribución de la partitura"
                        color: "#a9b6c9"
                        font.pixelSize: 12
                        font.bold: true
                    }

                    Label {
                        text: "Elige cuántos segmentos van en cada página."
                        color: "#687991"
                        font.pixelSize: 10
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }

                    ComboBox {
                        id: horizontalPagesCombo
                        Layout.fillWidth: true
                        Layout.preferredHeight: 38
                        model: ["1", "2", "3", "4"]
                        currentIndex: 0
                    }

                    RowLayout {
                        Layout.fillWidth: true

                        Label {
                            text: "Cortes: " + backend.layoutCutCount
                            color: "#dbe5f2"
                            font.pixelSize: 11
                            font.bold: true
                        }

                        Item { Layout.fillWidth: true }

                        Button {
                            Layout.preferredWidth: 92
                            Layout.preferredHeight: 30
                            text: "Limpiar"
                            enabled: backend.layoutCutCount > 0 && !backend.busy
                            onClicked: backend.clearLayoutCuts()
                        }
                    }

                    ListView {
                        id: cutList
                        Layout.fillWidth: true
                        Layout.preferredHeight: Math.min(
                            150,
                            Math.max(40, backend.layoutCutCount * 42)
                        )
                        clip: true
                        spacing: 4
                        model: backend.layoutCutCount
                        boundsBehavior: Flickable.StopAtBounds

                        delegate: Rectangle {
                            width: cutList.width
                            height: 38
                            radius: 7
                            color: "#111a28"
                            border.color: "#1b2a3f"

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 8
                                anchors.rightMargin: 8
                                spacing: 6

                                Label {
                                    Layout.preferredWidth: 48
                                    text: "Corte " + (index + 1)
                                    color: "#cbd5e3"
                                    font.pixelSize: 9
                                    font.bold: true
                                }

                                Slider {
                                    id: cutSlider
                                    Layout.fillWidth: true
                                    from: 2
                                    to: 98
                                    value: backend.layoutCutPercent(index)
                                    enabled: !backend.busy
                                    onMoved: backend.setLayoutCut(index, value / 100.0)
                                }

                                Label {
                                    Layout.preferredWidth: 38
                                    text: Math.round(cutSlider.value) + "%"
                                    color: "#7c8da4"
                                    font.pixelSize: 9
                                }

                                Button {
                                    Layout.preferredWidth: 24
                                    Layout.preferredHeight: 24
                                    text: "×"
                                    enabled: !backend.busy
                                    onClicked: backend.removeLayoutCut(index)
                                }
                            }
                        }
                    }

                    Label {
                        text: backend.layoutCutCount === 0
                              ? "También puedes agregar un corte desde la vista de reconstrucción."
                              : "Ajusta los cortes aquí o arrastra sus líneas sobre la reconstrucción."
                        color: "#687991"
                        font.pixelSize: 9
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                }
                Item { Layout.preferredHeight: 6 }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Button {
                Layout.fillWidth: true
                Layout.preferredHeight: 44
                text: "Vista previa"
                enabled: backend.frameCount > 0 && !backend.busy
                onClicked: backend.preview(parseInt(pagesCombo.currentText))
            }

            Button {
                Layout.fillWidth: true
                Layout.preferredHeight: 44
                text: "Generar PDF"
                enabled: backend.frameCount > 0 && !backend.busy
                onClicked: pdfDialog.open()
            }
        }
    }
}
