import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    color: "#0e1420"

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 22
        spacing: 8

        Label {
            text: "♫  ScoreCapture"
            color: "#f4f7fb"
            font.pixelSize: 23
            font.bold: true
            Layout.topMargin: 6
        }

        Label {
            text: "YouTube / Video → PDF"
            color: "#748198"
            font.pixelSize: 12
            Layout.bottomMargin: 20
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 44
            radius: 10
            color: "#1d6fff"

            Label {
                anchors.fill: parent
                anchors.leftMargin: 14
                text: "  Extraer partitura"
                verticalAlignment: Text.AlignVCenter
                color: "white"
                font.pixelSize: 13
                font.bold: true
            }
        }

        Label { text: "FLUJO"; color: "#627089"; font.pixelSize: 10; font.bold: true; Layout.topMargin: 18 }
        Label { text: "01  Fuente"; color: "#b9c4d6"; font.pixelSize: 13; Layout.topMargin: 6 }
        Label { text: "02  Recorte y rango"; color: "#8b98ad"; font.pixelSize: 13 }
        Label { text: "03  Exportar PDF"; color: "#8b98ad"; font.pixelSize: 13 }

        Item { Layout.fillHeight: true }

        Label {
            text: "Procesamiento en segundo plano\nNo requiere permisos de administrador."
            color: "#657188"
            font.pixelSize: 11
        }
    }
}
