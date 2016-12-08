from work.models import Ocp_Material_Type, Ocp_Nonmaterial_Type
from general.models import Artwork_Type

def get_rt_from_ocp_rt(gen_rt):
    rt = None
    if hasattr(gen_rt, 'resource_type') and gen_rt.resource_type:
        rt = gen_rt.resource_type
    else:
        if isinstance(gen_rt, Artwork_Type):
            try:
                grt = Ocp_Material_Type.objects.get(id=gen_rt.id)
                rt = grt.resource_type
            except:
                try:
                    grt = Ocp_Nonmaterial_Type.objects.get(id=gen_rt.id)
                    rt = grt.resource_type
                except:
                    rt = False
    return rt

def get_ocp_rt_from_rt(rt):
    gen_rt = None
    if hasattr(rt, 'ocp_resource_type') and rt.ocp_resource_type:
        gen_rt = rt.ocp_resource_type
    else:
        try:
            gen_rt = Ocp_Material_Type.objects.get(resource_type=rt)
        except:
            try:
                gen_rt = Ocp_Nonmaterial_Type.objects.get(resource_type=rt)
            except:
                gen_rt = False
    return gen_rt


def update_from_general(clas=None):
  news = ['news:']
  updt = ['updt:']
  if clas == "Material_Type":
    try:
      gen_mts = Material_Type.objects.all() #filter(lft__gte=typ.lft, rght__lte=typ.rght, tree_id=typ.tree_id)
      ocp_mts = Ocp_Material_Type.objects.all() #filter(lft__gte=typ.lft, rght__lte=typ.rght, tree_id=typ.tree_id)
      for mt in gen_mts:
        if not mt in ocp_mts:
          obj = Ocp_Material_Type.objects.create( #mt )
            #material_type = mt,
            id=mt.id,
            name=mt.name,
            description=mt.description,
            parent=mt.parent
          ).get()
          news.append(obj)
          #break
        else:
          #pass
          obj = Ocp_Material_Type.objects.filter(id=mt.id).update( #mt )
            id=mt.id,
            name=mt.name,
            description=mt.description,
          #  lft=mt.lft,
          #  rght=mt.rght,
          #  tree_id=mt.tree_id,
            parent=mt.parent
          ).get()
          updt.append(obj).append(update)
      return news.append(updt)
    except:
      pass

  elif clas == "Nonmaterial_Type":
    try:
      gen_nts = Nonmaterial_Type.objects.all() #filter(lft__gte=typ.lft, rght__lte=typ.rght, tree_id=typ.tree_id)
      ocp_nts = Ocp_Nonmaterial_Type.objects.all() #filter(lft__gte=typ.lft, rght__lte=typ.rght, tree_id=typ.tree_id)
      for nt in gen_nts:
        if not nt in ocp_nts:
          obj = Ocp_Nonmaterial_Type.objects.create( #nt )
            nonmaterial_type = nt,
            id=nt.id,
            name=nt.name,
            description=nt.description,
            parent=nt.parent
          ).get()
          news.append(obj)
          #break
        else:
          #pass
          obj = Ocp_Nonmaterial_Type.objects.filter(id=nt.id).update( #nt )
            id=nt.id,
            name=nt.name,
            description=nt.description,
            parent=nt.parent
          ).get()
          updt.append(obj)
      return news.append(updt)
    except:
      return 'error'
  else:
    return clas
