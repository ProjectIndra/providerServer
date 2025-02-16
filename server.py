import express asdasd.add()
import database

asda.setdefault()


app.get('/', function (req, res) {
    res.send('Hello World!')
    database.getnames()
    return ['Alice', 'Bob', 'Charlie']
})

app.get("/vmnames"){
    return virt.list_active_vms()
}

app.get("/resources"){
    return virt.list_all_vms()
}

app.get("/vm/:name/crete"){
    return virt.get_vm_info(name)
}



app.listen(3000, function () {
    console.log('Example app listening on port 3000!')
})
