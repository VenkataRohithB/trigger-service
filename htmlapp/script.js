document.addEventListener("DOMContentLoaded", function () {
    const gridOptions = {
        columnDefs: [
            { headerName: "ID", field: "id" },
            { headerName: "Trigger Name", field: "trigger_name" },
            { headerName: "Status", field: "status" },
            { headerName: "Triggered At", field: "triggered_at" },
            { headerName: "Trigger Type", field: "trigger_type" }
        ],
        rowData: []
    };

    const gridDiv = document.getElementById("myGrid");
    const gridApi = agGrid.createGrid(gridDiv, gridOptions);

    function fetchData() {
        fetch("http://localhost:8989/triggered_events/fetch_events")
            .then(response => response.json())
            .then(data => gridApi.setGridOption("rowData", data.records))
            .catch(error => console.error("Error fetching data:", error));
    }

    setInterval(fetchData, 5000);
    fetchData();
});

/* Open & Close Popup */
function openPopup() {
    document.getElementById("popup").classList.add("active");
}

function closePopup() {
    document.getElementById("popup").classList.remove("active");
}

/* Toggle Scheduled Options */
function toggleTriggerType() {
    document.getElementById("scheduledOptions").style.display = "none";
    document.getElementById("apiOptions").style.display = "none";

    if (document.getElementById("triggerType").value === "scheduled") {
        document.getElementById("scheduledOptions").style.display = "block";
    } else {
        document.getElementById("apiOptions").style.display = "block";
    }
}

/* Reset radio selection */
function toggleScheduleOptions() {
    document.getElementById("onetimeOptions").style.display = "none";
    document.getElementById("intervalOptions").style.display = "none";

    const selectedValue = document.querySelector('input[name="scheduleType"]:checked').value;
    document.getElementById(selectedValue + "Options").style.display = "block";
}
