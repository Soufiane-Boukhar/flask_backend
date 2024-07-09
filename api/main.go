package handler

import (
    "encoding/json"
    "fmt"
    "net/http"
    "os"
    "github.com/go-sql-driver/mysql"
    "database/sql"
)

type Response struct {
    Message string      `json:"message"`
    Data    interface{} `json:"data,omitempty"`
}

func indexHandler(w http.ResponseWriter, r *http.Request) {
    response := Response{Message: "Hello, World!"}
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(response)
}

func dataHandler(w http.ResponseWriter, r *http.Request) {
    dsn := fmt.Sprintf("%s:%s@tcp(%s)/%s",
        os.Getenv("avnadmin"),
        os.Getenv("AVNS_wWoRjEZRmFF5NgjGCcY"),
        os.Getenv("mysql-1fb82b3b-boukhar-d756.e.aivencloud.com"),
        os.Getenv("defaultdb"),
    )

    db, err := sql.Open("mysql", dsn)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    defer db.Close()

    rows, err := db.Query("SELECT * FROM contacts LIMIT 10")
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    defer rows.Close()

    var contacts []map[string]interface{}
    cols, _ := rows.Columns()
    for rows.Next() {
        columns := make([]interface{}, len(cols))
        columnPointers := make([]interface{}, len(cols))
        for i := range columns {
            columnPointers[i] = &columns[i]
        }
        rows.Scan(columnPointers...)
        contact := make(map[string]interface{})
        for i, colName := range cols {
            val := columnPointers[i].(*interface{})
            contact[colName] = *val
        }
        contacts = append(contacts, contact)
    }

    response := Response{Message: "Data fetched successfully", Data: contacts}
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(response)
}

func Handler(w http.ResponseWriter, r *http.Request) {
    switch r.URL.Path {
    case "/":
        indexHandler(w, r)
    case "/data":
        dataHandler(w, r)
    default:
        http.NotFound(w, r)
    }
}

func main() {
    http.HandleFunc("/", Handler)
    http.HandleFunc("/data", Handler)
    http.ListenAndServe(":3000", nil)
}
