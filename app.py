from flask import Flask, render_template, request, redirect, url_for, session,Response
from pymongo import MongoClient
# import xlwt
import io
from random import randint,choices
# from flask_mail import Mail,Message
from datetime import datetime
import string
import certifi
ca = certifi.where()

app = Flask(__name__)
# mail = Mail(app)

# app.config['MAIL_SERVER']='smtp.gmail.com'
# app.config['MAIL_PORT'] = 465
# app.config['MAIL_USERNAME'] = 'formsappp@gmail.com'
# app.config['MAIL_PASSWORD'] = 'formsapp@2021'
# app.config['MAIL_USE_TLS'] = False
# app.config['MAIL_USE_SSL'] = True
# mail = Mail(app)

cluster = MongoClient("mongodb+srv://Admin:admin@billboard.k6x1l.mongodb.net/myFirstDatabase?retryWrites=true&w=majority",tlsCAFile=ca)
#mongodb+srv://Admin:admin@billboard.k6x1l.mongodb.net/myFirstDatabase?retryWrites=true&w=majority
db = cluster["Billboard"]
users = db["Users"]
bills = db["Bills"]
items = db["Itemlists"]
cart = db["Cart"]
invoices = db["Invoices"]
app.secret_key =  "b'_5#y2LF4Q8z\n\xec]/'"


@app.route("/",methods = ["POST","GET"])
def login():
    test = users.find_one({"username":"test"})
    print(test["password"])
    if "orgoid" in session:
        return redirect(url_for("home"))
    else:
        if request.method=="POST":
            uname = request.form["username"]
            pw = request.form["password"]
            user = users.find_one({"username":uname})
            if user == None:
                return render_template("login.html",Invalid_Credentials="Organisation does not exist")
            else:
                if user["password"] == pw:
                    session["orgoid"] = user["_id"]
                    return redirect(url_for("home"))
                else:
                    return render_template("login.html",Invalid_Credentials="Invalid Credentials")
        return render_template("login.html")

@app.route("/register",methods = ["POST","GET"])
def register():
    if request.method == "POST":
        uname = request.form["username"]
        email = request.form["email"]
        pw = request.form["password"]
        conf = request.form["confirm"]
        if pw != conf:
            return render_template("Register.html",Invalid_Credentials="Password does not match",username=uname,email=email)
        elif users.find_one({"username":uname}):
            return render_template("Register.html",Invalid_Credentials="Organisation already exists",email=email,password=pw)
        elif users.find_one({"email":email}):
            return render_template("Register.html",Invalid_Credentials="Email already exists",username=uname,password=pw)
        else:
            id = randint(0,99999999999999)+ randint(0,99999999)
            session["orgoid"] = id
            users.insert_one({"_id":id,"username":uname,"email":email,"password":pw,"Isent":0,"Irec":0,"Bsent":0,"Brec":0,"categories":"","itemcount":0})
            return redirect(url_for("home"))
    else:
        return render_template("Register.html")

@app.route("/home",methods = ["POST","GET"])
def home():
    if "orgoid" in session:
        id = session["orgoid"]
        user = users.find_one({"_id":id})
        categories = user["categories"].strip().split(',')
        if request.method=="POST":
            itemid = request.form["itemid"]
            pname = request.form["name"]
            category = request.form.get("category")
            print(itemid,pname,category)
            if itemid=="" and pname=="" and category==None:
                item_lists = items.find({"uid":id})
                return render_template("home.html",search=True,items = item_lists,name=user["username"],Isent=user["Isent"],Irec=user["Irec"],Bsent=user["Bsent"],Brec=user["Brec"],categories=categories)
            elif itemid!="" and pname!="":
                lists = items.find({"uid":id})
                item_lists = []
                for item in lists:
                    if itemid in item["_id"] and pname in item["product_name"]:
                        item_lists.append(item)
                return render_template("home.html",search=True,items = item_lists,name=user["username"],Isent=user["Isent"],Irec=user["Irec"],Bsent=user["Bsent"],Brec=user["Brec"],categories=categories)
            elif itemid!="":
                lists = items.find({"uid":id})
                item_lists = []
                for item in lists:
                    if itemid in item["_id"]:
                        item_lists.append(item)
                return render_template("home.html",search=True,items = item_lists,name=user["username"],Isent=user["Isent"],Irec=user["Irec"],Bsent=user["Bsent"],Brec=user["Brec"],categories=categories)
            elif pname!="":
                lists = items.find({"uid":id})
                item_lists = []
                for item in lists:
                    if pname in item["product_name"]:
                        item_lists.append(item)
                return render_template("home.html",search=True,items = item_lists,name=user["username"],Isent=user["Isent"],Irec=user["Irec"],Bsent=user["Bsent"],Brec=user["Brec"],categories=categories)
            else:
                return render_template("home.html",search=False,name=user["username"],Isent=user["Isent"],Irec=user["Irec"],Bsent=user["Bsent"],Brec=user["Brec"],categories=categories)
        else:
            return render_template("home.html",search=False,name=user["username"],Isent=user["Isent"],Irec=user["Irec"],Bsent=user["Bsent"],Brec=user["Brec"],categories=categories)
    else:
        return redirect(url_for("login"))


@app.route("/addToCart/<pid>")
def addCart(pid):
    if "orgoid" in session:
        id = session["orgoid"]
        cartitems = cart.find_one({"uid":id})
        if cartitems == None:
            itemlists = {}
            itemlists[pid] = 1
            cart.insert_one({"uid":id,"items":itemlists})
            return None
        else:
            itemlists = cartitems["items"]
            if pid in itemlists:
                itemlists[pid] += 1
            else:
                itemlists[pid] = 1
            cart.update_one({"uid":id},{"$set":{"items":itemlists}})
            return None
    else:
        return redirect(url_for("login"))


@app.route("/logout")
def logout():
    if "orgoid" in session:
        session.pop("orgoid",None)
        return redirect(url_for("login"))
    else:
        return redirect(url_for("login"))



@app.route("/addItems",methods=["POST","GET"])
def addItems():
    if "orgoid" in session:
        print(request.path)
        id = session["orgoid"]
        user = users.find_one({"_id":id})
        categories = user["categories"].strip().split(',')
        item_lists = items.find({"uid":id})
        if request.method=="POST":
            name = request.form["Product_Name"]
            category = request.form.get("category")
            price = int(request.form["price"])
            discount = int(request.form["discount"])
            pid = category[0:3] + str(randint(0,999))
            items.insert_one({"_id":pid,"uid":id,"product_name":name,"category":category,"price":price,"discount":discount})
            return redirect(url_for("addItems"))
        else:
            return render_template("addItems.html",categories=categories,item_lists=item_lists)
    else:
        return redirect(url_for("login"))


@app.route("/deleteItem/<id>",methods=["POST","GET"])
def deleteItem(id):
    if "orgoid" in session:
        orgoid = session["orgoid"]
        items.delete_one({"_id":id,"uid":orgoid})
        itemcount = users.find_one({"_id":orgoid})["itemcount"] - 1
        users.update_one({"_id":orgoid},{"$set":{"itemcount":itemcount}})
        return redirect(url_for("addItems"))
    else:
        return redirect(url_for("login"))


@app.route("/editItem/<id>",methods=["POST","GET"])
def editItem(id):
    if "orgoid" in session:
        orgoid = session["orgoid"]
        user = users.find_one({"_id":orgoid})
        categories = user["categories"].strip().split(',')
        itemlists = items.find_one({"_id":id,"uid":orgoid})
        if request.method=="POST":
            name = request.form["Product_Name"]
            item = items.find_one({"product_name":name})
            print(item)
            if item==None:
                category = request.form.get("category")
                price = request.form["price"]
                discount = request.form["discount"]
                items.update_one({"_id":id},{"$set":{"product_name":name,"price":int(price),"discount":int(discount),"category":category}})
                return redirect(url_for("addItems"))
            if item!=None and item["_id"]==id:
                category = request.form.get("category")
                price = request.form["price"]
                discount = request.form["discount"]
                items.update_one({"_id":id},{"$set":{"product_name":name,"price":int(price),"discount":int(discount),"category":category}})
                return redirect(url_for("addItems"))
            else:
                return render_template("editItem.html",item=itemlists,categories=categories,invalid="Product name already exist")
        else:
            return render_template("editItem.html",item=itemlists,categories=categories,invalid="")
    else:
        return redirect(url_for("login"))


@app.route("/account",methods=["POST","GET"])
def account():
    if "orgoid" in session:
        id = session["orgoid"]
        user=users.find_one({"_id":id})
        if request.method == "POST":
            orgoname = request.form["username"]
            email = request.form["email"]
            categories = request.form["categories"]
            pw = request.form["password"]
            if pw=="":
                return render_template("account.html",uname=user["username"],email=user["email"],categories=user["categories"],Invalid_Credentials="Length of Password must be more than 0")
            if email!=user["email"] and users.find_one({"email":email}):
                return render_template("account.html",uname=user["username"],pw=user["password"],categories=user["categories"],Invalid_Credentials="Email already exists")
            if user["username"]!=orgoname and users.find_one({"username":orgoname}):
                return render_template("account.html",email=user["email"],pw=user["password"],categories=user["categories"],Invalid_Credentials="Organisation already exists")
            users.update_one({"_id":id},{"$set":{"username":orgoname,"email":email,"password":pw,"Isent":user["Isent"],"Irec":user["Irec"],"Bsent":user["Bsent"],"Brec":user["Brec"],"categories":categories}})
            user=users.find_one({"_id":id})
            return render_template("account.html",uname=user["username"],email=user["email"],pw=user["password"],categories=user["categories"])
        else:
            return render_template("account.html",uname=user["username"],email=user["email"],pw=user["password"],categories=user["categories"])
    else:
        return redirect(url_for("login"))


@app.route("/invoices",methods=["POST","GET"])
def invoice():
    if "orgoid" in session:
        id = session["orgoid"]
        isent = invoices.find({"sid":id})
        irec = invoices.find({"rid":id})
        Invs = []
        for store in isent:
            Inv = {}
            Inv["receiver"] = users.find_one({"_id":store["rid"]})["username"]
            Inv["products"] = ""
            for item in store["items"]:
                Inv["products"] += items.find_one({"_id":item})["product_name"]+"("+str(store["items"][item])+"),\n"
            Inv["total"] = store["total"]
            Inv["time"] = store["time"]
            Inv["status"] = store["status"]
            Inv["id"] = store["_id"]
            Invs.append(Inv)
        Invr = []
        for store in irec:
            Inv = {}
            Inv["sender"] = users.find_one({"_id":store["sid"]})["username"]
            Inv["products"] = ""
            for item in store["items"]:
                Inv["products"] += items.find_one({"_id":item})["product_name"]+"("+str(store["items"][item])+"),\n"
            Inv["total"] = store["total"]
            Inv["time"] = store["time"]
            Inv["status"] = store["status"]
            Inv["id"] = store["_id"]
            if Inv["status"]!="Declined":
                Invr.append(Inv)
        Invs.reverse()
        Invr.reverse()
        return render_template("invoices.html",Isent=Invs,Irec=Invr)
    else:
        return redirect(url_for("login"))

@app.route("/deleteInv/<id>")
def deleteInv(id):
    if "orgoid" in session:
        orgoid = session["orgoid"]
        users.update_one({"_id":orgoid},{"$set":{"Isent":users.find_one({"_id":orgoid})["Isent"]-1}})
        rid = invoices.find_one({"_id":id,"sid":orgoid})["rid"]
        users.update_one({"_id":rid},{"$set":{"Irec":users.find_one({"_id":rid})["Irec"]-1}})
        invoices.delete_one({"sid":orgoid,"_id":id})
        return redirect(url_for("invoice"))
    else:
        return redirect(url_for("login"))


@app.route("/accept/<id>")
def accept(id):
    if "orgoid" in session:
        orgoid = session["orgoid"]
        curr = invoices.find_one({"_id":id,"rid":orgoid})
        curr.pop("status")
        curr["time"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        bills.insert_one(curr)
        users.update_one({"_id":orgoid},{"$set":{"Brec":users.find_one({"_id":orgoid})["Brec"]+1}})
        sid = invoices.find_one({"_id":id,"rid":orgoid})["sid"]
        users.update_one({"_id":sid},{"$set":{"Bsent":users.find_one({"_id":sid})["Bsent"]+1}})
        invoices.delete_one({"_id":id,"rid":orgoid})
        return redirect(url_for("invoice"))
    else:
        return redirect(url_for("login"))

@app.route("/decline/<id>")
def decline(id):
    if "orgoid" in session:
        orgoid = session["orgoid"]
        invoices.update_one({"_id":id,"rid":orgoid},{"$set":{"status":"Declined"}})
        return redirect(url_for("invoice"))
    else:
        return redirect(url_for("login"))

@app.route("/recart/<id>")
def recart(id):
    if "orgoid" in session:
        orgoid = session["orgoid"]
        cart.delete_one({"uid":orgoid})
        cartitems = invoices.find_one({"_id":id,"sid":orgoid})
        users.update_one({"_id":orgoid},{"$set":{"Isent":users.find_one({"_id":orgoid})["Isent"]-1}})
        rid = invoices.find_one({"_id":id,"sid":orgoid})["rid"]
        users.update_one({"_id":rid},{"$set":{"Irec":users.find_one({"_id":rid})["Irec"]-1}})
        invoices.delete_one({"_id":id,"sid":orgoid})
        cartitems.pop("total")
        cartitems.pop("time")
        cartitems.pop("status")
        cartitems.pop("rid")
        cartitems["uid"] = cartitems["sid"]
        cartitems.pop("sid")
        cart.insert_one(cartitems)
        return redirect(url_for("cartdetails"))
    else:
        return redirect(url_for("login"))


@app.route("/bills",methods=["POST","GET"])
def bill():
    if "orgoid" in session:
        id = session["orgoid"]
        bsent = bills.find({"sid":id})
        brec = bills.find({"rid":id})
        billsent = []
        for store in bsent:
            bil = {}
            bil["receiver"] = users.find_one({"_id":store["rid"]})["username"]
            bil["time"] = store["time"]
            bil["total"] = 0
            bil["products"] = []
            for item in store["items"]:
                products = {}
                itemdetails = items.find_one({"_id":item})
                products["name"] = itemdetails["product_name"]
                products["Quantity"] = store["items"][item]
                products["price"] = itemdetails["price"]
                products["total"] = products["price"]*products["Quantity"]
                bil["total"] += products["total"]
                bil["products"].append(products)
            print(bil)
            billsent.append(bil)
        billrec = []
        for store in brec:
            bil = {}
            bil["sender"] = users.find_one({"_id":store["sid"]})["username"]
            bil["time"] = store["time"]
            bil["total"] = 0
            bil["products"] = []
            for item in store["items"]:
                products = {}
                itemdetails = items.find_one({"_id":item})
                products["name"] = itemdetails["product_name"]
                products["Quantity"] = store["items"][item]
                products["price"] = itemdetails["price"]
                products["total"] = products["price"]*products["Quantity"]
                bil["total"] += products["total"]
                bil["products"].append(products)
            print(bil)
            billrec.append(bil)
        return render_template("bills.html",bsen=billsent,brec=billrec)
    else:
        return redirect(url_for("login"))

@app.route("/cart",methods=["POST","GET"])
def cartdetails():
    if "orgoid" in session:
        id = session["orgoid"]
        cartitems = cart.find_one({"uid":id})
        if cartitems==None:
            return render_template("cart.html",Notfound=True)
        total = 0
        itemlists = []
        for x in cartitems["items"]:
            item = {}
            itemdetails = items.find_one({"_id":x,"uid":id})
            item["_id"] = x
            item["quantity"] = cartitems["items"][x]
            item["name"] = itemdetails["product_name"]
            item["price"] = itemdetails["price"] - itemdetails["discount"]
            item["total"] = item["quantity"]*item["price"]
            total += item["total"]
            itemlists.append(item)
        if request.method=="POST":
            name = request.form["orgo_name"]
            receiver = users.find_one({"username":name})
            if receiver==None:
                return render_template("cart.html",Notfound=False,items=itemlists,total=total,alt="Given organisation does not exist")
            else:
                inv = {}
                inv["sid"] = id
                inv["rid"] = receiver["_id"]
                inv["_id"] = ''.join(choices(string.ascii_uppercase + string.digits, k = 10))
                inv["items"] = cartitems["items"]
                inv["total"] = total
                inv["time"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                inv["status"] = "Active"
                invoices.insert_one(inv)
                users.update_one({"_id":inv["sid"]},{"$set":{"Isent":users.find_one({"_id":inv["sid"]})["Isent"] + 1}})
                users.update_one({"_id":inv["rid"]},{"$set":{"Irec":users.find_one({"_id":inv["sid"]})["Irec"] + 1}})
                cart.delete_one({"uid":id})
                return redirect(url_for('cartdetails'))
        else:
            if total == 0:
                cart.delete_one({"uid":id})
                return render_template("cart.html",Notfound=True)
            else:
                return render_template("cart.html",items=itemlists,total=total)
    else:
        return redirect(url_for("login"))

@app.route("/decrement/<pid>")
def decrement(pid):
    if "orgoid" in session:
        id = session["orgoid"]
        cartitems = cart.find_one({"uid":id})
        itemlists = cartitems["items"]
        if itemlists[pid] == 1:
            itemlists.pop(pid)
        else:
            itemlists[pid] -= 1
        cart.update_one({"uid":id},{"$set":{"items":itemlists}})
        return redirect(url_for("cartdetails"))
    else:
        return redirect(url_for("login"))

@app.route("/increment/<pid>")
def increment(pid):
    if "orgoid" in session:
        id = session["orgoid"]
        cartitems = cart.find_one({"uid":id})
        itemlists = cartitems["items"]
        itemlists[pid] += 1
        cart.update_one({"uid":id},{"$set":{"items":itemlists}})
        return redirect(url_for("cartdetails"))
    else:
        return redirect(url_for("login"))


@app.route("/deleteCart")
def deleteCart():
    if "orgoid" in session:
        id = session["orgoid"]
        if cart.find_one({"uid":id}):
            cart.delete_one({"uid":id})
        return redirect(url_for("cartdetails"))
    else:
        return redirect(url_for("login"))



if __name__ == "__main__":
    app.run(debug=True)








































"""
@app.route("/",methods = ["POST","GET"])
def login():
    if "id" in session:
        return redirect(url_for("dashboard"))
    else:
        if request.method == "POST":
            user = request.form["username"]
            pw = request.form["password"]
            validate = users.find_one({"username":user})
            if validate == None:
                return render_template("login.html",uflash="Username does not exist")
            pcheck = validate["password"]
            if pw == pcheck:
                session["id"] = validate["_id"]
                return redirect(url_for("dashboard"))
            else:
                return render_template("login.html",flash="Invalid Username or password")
        return render_template("login.html")


@app.route("/register",methods = ["POST","GET"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        user = request.form["username"]
        pw = request.form["password"]
        cpw = request.form["confirm"]
        if pw == cpw:
            validate = users.find_one({"username":user})
            if validate != None:
                return render_template("Register.html",uflash="Username already exists",email=email,pw=pw,cpw=cpw)
            else:
                validate = users.find_one({"email":email})
                print(validate)
                if validate == None:
                    id = randint(0,99999999999999)+ randint(0,99999999)
                    users.insert_one({"_id":id,"username":user,"email":email,"password":pw})
                    session["id"] = id 
                    return redirect(url_for("dashboard"))
                else:
                    return render_template("Register.html",eflash="Email already exists",username=user,pw=pw,cpw=cpw)
        else:
            return render_template("Register.html",flash="Password does not match",username=user,email=email)
    else:
        return render_template("Register.html")


@app.route("/forgot/mail",methods=["GET","POST"])
def forgot():
    if "id" in session:
        return redirect(url_for("dashboard"))
    else:
        if request.method == "POST":
            email = request.form["mail"]
            user = users.find_one({"email":email})
            if user != None:
                msg = Message( 
                    'Formsapp - Forgot your Password', 
                    sender ='formsappp@gmail.com', 
                    recipients = [email] 
                    ) 
                msg.body = 'Hello '+user["username"]+" you seem to forgot your password.\n"+"Your Username : "+user["username"]+"\nYour Password : "+user["password"]          
                mail.send(msg)
            else:
                msg = Message('Formsapp - Mail Not Found',sender ='formsappp@gmail.com',recipients = [email]) 
                msg.body = "You have no account on formsapp. You may given or chaged another mail in our app"
                mail.send(msg)
            return redirect(url_for("login"))
        else:
            return render_template("forgot.html")



@app.route("/dashboard")
def dashboard():
    if "id" in session:
        id = session['id']
        form = forms.find({"userid":id})
        if form == None:
            return render_template("dashboard.html")
        else:
            titles = []
            for x in form:
                temp = {"title":x["title"],"link":x["_id"]}
                titles.append(temp)
            valid = True
            return render_template("dashboard.html",titles=titles,valid=valid)
    else:
        return redirect(url_for("login"))

@app.route("/acc",methods=["POST","GET"])
def acc():
    if request.method == "POST":
        mail = request.form["email"]
        un = request.form["username"]
        pw = request.form["password"]
        cpw = request.form["confirm"]
        id = session["id"]
        userinfo = users.find_one({"_id":id})
        if pw == cpw:
            uvar = users.find_one({"username":un})
            if uvar!= None and uvar["_id"] != id:
                un = userinfo["username"]
                email = userinfo["email"]
                pw = userinfo["password"]
                return render_template("myacc.html",uname = un,mail = email, passw = pw,uflash="Username already exists")
            else:
                users.update_one({"_id":id},{"$set":{"email":mail,"username":un,"password":pw}})
                return redirect(url_for("acc"))
        else:
            un = userinfo["username"]
            email = userinfo["email"]
            pw = userinfo["password"]
            return render_template("myacc.html",uname = un,mail = email, passw = pw,uflash="Password does not match")
    elif "id" in session:
        id = session["id"]
        userinfo = users.find_one({"_id":id})
        un = userinfo["username"]
        email = userinfo["email"]
        pw = userinfo["password"]
        return render_template("myacc.html",uname = un,mail = email, passw = pw)
    else:
        return redirect(url_for("login"))
    

@app.route("/form/create")
def formcreate():
    formid = randint(0,99999999)+ randint(0,99999999)
    return redirect(url_for("form",formid=formid))

@app.route("/delete/<formid>")
def formdelete(formid):
    forms.remove({'_id':formid})
    respform.remove({"form-id":formid})
    return redirect(url_for('dashboard'))

@app.route("/form/<formid>",methods=["POST","GET"])
def form(formid):
    if "id" in session:
        if request.method=="POST":
            title = request.form["title"]
            qcount = request.form["qcount"]
            maxtime = request.form["mtime"]
            questions = request.form.getlist("question")
            correct = request.form.getlist("correct")
            Questions = []

            for x in range(1,int(qcount)+1):
                type = request.form["question-type-"+str(x)]
                required = request.form["required-"+str(x)]
                options = request.form.getlist("option-"+str(x))   
                checked1 = ["checked",""] if type=="Single" else ["","checked"]
                checked2 = ["checked",""] if required=="yes" else ["","checked"]
                print(checked1,checked2)
                type = "radio" if type=="Single" else "checkbox"
                required = "true" if required=="yes" else "false"
                question = {"no":x,"question":questions[x-1],"options":options,"correct":correct[x-1],"required":required,"type":type,"check1":checked1,"check2":checked2}
                Questions.append(question)
            id = session["id"]
            valid = forms.find_one({"_id":formid})
            
            if valid == None:
                form ={"userid":id,"_id":formid,"title":title,"count":qcount,"time":maxtime,"questions":Questions}
                forms.insert_one(form)
            else:
                forms.update_one({"_id":formid},{"$set":{"title":title,"count":qcount,"time":maxtime,"questions":Questions}})
            return redirect(url_for("form",formid=formid))
        else:
            id = session["id"]
            info = forms.find_one({"_id":formid,"userid":id})
            valid = True if info!= None else False
            invalid = True if forms.find_one({"_id":formid})!=None and valid == False else False
            return render_template("formcreate.html",info = info,valid = valid,invalid = invalid)
    else:
        return redirect(url_for("login"))

@app.route("/after")
def after():
    return render_template("get.html")

@app.route('/respond/<formid>',methods=['POST','GET'])
def response(formid):
    info = forms.find_one({"_id":formid})
    if request.method=="POST":
        respid = request.form["resp-id"]
        answers = []
        for x in range(int(info['count'])):
            temp = request.form.getlist("option-"+str(x+1))
            answers.append(temp)
        now = datetime.now()
        time = now.strftime("%d/%m/%Y %H:%M:%S")
        response = {"form-id":formid,"resp-id":respid,"answers":answers,'time':time}
        print(response)
        respform.insert_one(response)
        return redirect(url_for("after"))
    else:
        responseforms = []
        for x in info["questions"]:
            temp = []
            temp.append(x["question"])
            temp.append(x['type'])
            temp.append(x['required'])
            temp.append(x['options'])
            responseforms.append(temp)
        valid = True if "id" in session else False
        return render_template("response.html",rforms = responseforms,title=info['title'],valid=valid,time =info["time"] )

@app.route('/get/<formid>',methods=['POST','GET'])
def get(formid):
    info = forms.find_one({"_id":formid})
    output = io.BytesIO()
    workbook = xlwt.Workbook()
    
    sh = workbook.add_sheet(info["title"])

    sh.write(0,0,"Title of the Form : "+info["title"])
    sh.write(1,0,"Maximum time given : "+str(info["time"]))
    sh.write(2,0,"Number of questions : "+str(info["count"]))
    sh.write(3,0,"")
    sh.write(4,0,"S.No")
    sh.write(4,1,"Responder-Id")
    sh.write(4,len(info["questions"])+2,"Submission Time")
    sh.write(5,1,"Answers")
    for x in range(len(info["questions"])):
        sh.write(4,x+2,info["questions"][x]['question'])
        sh.write(5,x+2,info["questions"][x]['correct'])
    
    sh.write(6,0,"")
    fullresponses = respform.find({"form-id":formid})
    responses = []
    for x in fullresponses:
        responses.append(x)
    for x in range(len(responses)):
        sh.write(7+x,0,str(x+1))
        sh.write(7+x,1,responses[x]['resp-id'])
        sh.write(7+x,len(info["questions"])+2,responses[x]['time'])
        for y in range(len(responses[x]['answers'])):
            sh.write(7+x,2+y,"|".join(str(x) for x in responses[x]['answers'][y]))

    workbook.save(output)
    output.seek(0)
    return Response(output,mimetype="application/ms-excel",headers={"Content-Disposition":"attachment;filename="+info["title"]+".xls"})



@app.route('/logout')
def logout():
	if "id" in session:
		session.pop("id",None)
		return redirect(url_for("login"))
	else:
		return redirect(url_for('login'))


"""
