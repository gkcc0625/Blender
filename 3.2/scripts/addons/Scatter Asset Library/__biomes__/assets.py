import bpy, os

#website adress:
#@https://twitter.com/dorianborremans?lang=en

blend  = 'scatter_#_part1.blend'

oblist = ('Sc Clovers 01'                       +'_#_'+
          'Sc Clovers 02'                       +'_#_'+
          'Sc Clovers 03'                       +'_#_'+
          'Sc Daisies'                          +'_#_'+
          'Sc Dandelion 01'                     +'_#_'+
          'Sc Dandelion 02'                     +'_#_'+
          'Sc Dandelion 03'                     +'_#_'+
          'Sc Grass 01'                         +'_#_'+
          'Sc Grass 02'                         +'_#_'+
          'Sc Grass Clump 01'                   +'_#_'+
          'Sc Grass Clump 02'                   +'_#_'+
          'Sc Grass Clump 03'                   +'_#_'+
          'Sc Grass Dry 01'                     +'_#_'+
          'Sc Grass tiny 01'                    +'_#_'+
          'Sc Grass Wild Clump 01'              +'_#_'+
          'Sc Grass Wild Clump 02'              +'_#_'+
          'Sc Grass Wild Clump Dry 01'          +'_#_'+
          'Sc Leaves 01'                        +'_#_'+
          'Sc Leaves 02'                        +'_#_'+
          'Sc Nettle 01'                        +'_#_'+
          'Sc Nettle 02'                        +'_#_'+
          'Sc PaperWhite'                       +'_#_'+
          'Sc Red poppy 01'                     +'_#_'+
          'Sc Weed 01'                          +'_#_'+
          'Sc Weed 02'                          +'_#_'+
          'Sc Grass Duo 01'                     +'_#_'+
          'Sc Grass Duo 02'                     +'_#_'+
          'Sc Frozen Nettle'                    +'_#_'+
          'Sc Frozen Grass Wild'                +'_#_'+
          'Sc Frozen Grass Clump'               +'_#_'+
          'Sc Frozen Grass'                     +'_#_'+
          'Sc Frozen Leaves'                    +'_#_'+
          'Sc Snowy Leaves'                     +'_#_'+
          'Sc Snowy Grass'                      +'_#_'+
          'Sc Snowy Grass Clump'                +'_#_'+
          'Sc Snowpile Small'                   +'_#_'+
          'Sc Snowpile Medium'                  +'_#_'+
          #Extra User Infos
          'Sc z_Info'                           +'_#_'+
          'Sc z_Info.001'                       +'_#_'+
          'Sc z_Info.002'                       +'_#_'+
          'Sc z_Info.003'                       )


bpy.ops.scatter.execute_assets(blend=blend,oblist=oblist)

"""#DESCRIPTION_START
Import all Scatter assets from B01.blend
(there's lots of assets, may take a minute) 
"""#DESCRIPTION_STOP

