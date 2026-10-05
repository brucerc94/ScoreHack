import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

ApplicationWindow {
    id: window

    visible: true

    // Fixed window size calculated from the full content stack:
    // header + source + main workspace + activity + spacing/margins.
    width: 1080
    height: 950
    minimumWidth: 1080
    maximumWidth: 1080
    minimumHeight: 950
    maximumHeight: 950

    flags: Qt.Window
           | Qt.WindowTitleHint
           | Qt.WindowSystemMenuHint
           | Qt.WindowMinimizeButtonHint
           | Qt.WindowCloseButtonHint

    title: "ScoreCapture — Extractor de Partituras"
    color: "#0b0f17"

    RowLayout {
        anchors.fill: parent
        spacing: 0

        AppSidebar {
            Layout.preferredWidth: 230
            Layout.fillHeight: true
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            ColumnLayout {
                width: Math.max(760, parent.width - 48)
                x: 24
                spacing: 14

                RowLayout {
                    Layout.fillWidth: true
                    Layout.topMargin: 18

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 3

                        Label {
                            text: "Extraer una partitura"
                            color: "#f4f7fb"
                            font.pixelSize: 29
                            font.bold: true
                        }

                        Label {
                            text: backend.status
                            color: "#8190a8"
                            font.pixelSize: 13
                        }
                    }

                    BusyIndicator {
                        running: backend.busy
                        Layout.preferredWidth: 28
                        Layout.preferredHeight: 28
                    }
                }

                SourceCard {}

                RowLayout {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 500
                    spacing: 14

                    PreviewCard {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                    }

                    SettingsCard {}
                }

                ActivityCard {
                    Layout.preferredHeight: 160
                }

                Item { Layout.preferredHeight: 10 }
            }
        }
    }
}
