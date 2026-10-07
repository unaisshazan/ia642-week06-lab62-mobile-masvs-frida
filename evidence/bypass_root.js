Java.perform(function () {
  var Root = Java.use("sg.vantagepoint.a.c");
  Root.a.implementation = function () {
    console.log("[root] c.a() -> false");
    return false;
  };
  Root.b.implementation = function () {
    console.log("[root] c.b() -> false");
    return false;
  };
  Root.c.implementation = function () {
    console.log("[root] c.c() -> false");
    return false;
  };

  var Crypto = Java.use("sg.vantagepoint.a.a");
  Crypto.a.overload("[B", "[B").implementation = function (key, ct) {
    var pt = this.a(key, ct);
    var s = Java.use("java.lang.String").$new(pt);
    console.log("[crypto] secret = " + s);
    send({ secret: String(s) });
    return pt;
  };
  console.log("[*] hooks installed");
});
