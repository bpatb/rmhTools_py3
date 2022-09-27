/*		Bake Parented Transform
		Bakes the transform of a parented layer into an unparented layer
		combines orientation and rotation and bakes keys into rotation
		Affects the length of the layer from in point to out point

		By: Michael Gochoco
            support@blurrypixel.com
            Version 1.06
		December 2010
		
		1.05	Now ignores audio layers and light layers with limited transforms
		1.06	Fixed bug with Cameras and Lights not responding correctly when dimensions are separated
*/
{
	var proj = app.project;
    var progBarUI = buildProgressBarUI(" Progress",300,40);                         
	var totalDurationToBake = 0;
	var progTime = 0;
	var StartBake = 0;
	var EndBake = 0;

	// FUNCTIONS:
     function buildProgressBarUI (windowTitle,windowWidth,windowHeight)
     {  //windowWidth and windowWidth are optional and are there to compensate for a lot of text if using the progressText feature
        if (windowWidth == null) windowWidth = 300;
        if (windowHeight == null) windowHeight = 20;
        
        var dlg = new Window("palette", windowTitle, undefined, {resizeable:false});
        var res = 
            "group { \
            orientation:'column', alignment:['left','top'], alignChildren:['fill','fill'],  \
               progress: Group { \
                    alignment:['fill','top'], alignChildren:['fill','top'], \
                    val: Progressbar {  }, \
                }, \
                text: Group { \
                    text: StaticText { preferredSize: ["+windowWidth+","+windowHeight+"], alignment:['left','top'], properties:{multiline:true} }, \
               } \
            };";

        dlg.grp = dlg.add(res);
        dlg.layergrp = dlg.add(res);
        
        dlg.center();
        
        return dlg;	
    } // close progressUI () 

    function updateProgBar(progBarUIObj,isLayerProgress,barValue,barMaxValue,progressText)
    {  //progressText is optional.  Use it if you want to display updating text under the progress bar
        var progBar = null;	
        var progText = null;
        if(isLayerProgress)
        {
            progBar = progBarUIObj.layergrp.progress.val;
            progText = progBarUIObj.layergrp.text.text;
        }
        else
        {
            progBar = progBarUIObj.grp.progress.val;	
            progText = progBarUIObj.grp.text.text;
        }
    
        if (progressText == null) progressText = "";  

        progBar.maxvalue = barMaxValue;
        progBar.value = (barValue==0)?0.01:barValue;
        progText.text = progressText;

        if (parseFloat(app.version) >= 9) progBar.window.update();  // This call refreshes the UI and fixes the Mac CS3 bug, but works in CS4 and above only.
    }

	function radiansToDegrees(r) 
	{
		return r * (180 / Math.PI);
	}

	function degreesToRadians(d) 
	{
		return d * ( Math.PI / 180 );
	}
    
	function eulerToMatrix(angle,x,y,z)
	{
		var result = [];
		result[0] = (1-Math.cos(angle))*x*x + Math.cos(angle);
		result[1] = (1-Math.cos(angle))*x*y - Math.sin(angle) * z;
		result[2] = (1-Math.cos(angle))*x*z + Math.sin(angle) * y;
		result[3] = 0;

		result[4] = (1-Math.cos(angle))*x*y + Math.sin(angle) * z;
		result[5] = (1-Math.cos(angle))*y*y + Math.cos(angle);
		result[6] = (1-Math.cos(angle))*y*z - Math.sin(angle) * x;
		result[7] = 0;

		result[8] = (1-Math.cos(angle))*x*z - Math.sin(angle)*y;
		result[9] = (1-Math.cos(angle))*y*z + Math.sin(angle)*x;
		result[10] = (1-Math.cos(angle))*z*z + Math.cos(angle);
		result[11] = 0;

		result[12] = 0;
		result[13] = 0;
		result[14] = 0;
		result[15] = 1;

		return  result;
	}

	function matrixMultiply(ref1,ref2)
	{
		var result = [];
		result[0] = ref1[0] * ref2[0] + ref1[1] * ref2[4] + ref1[2] * ref2[8] + ref1[3] * ref2[12];
		result[1] = ref1[0] * ref2[1] + ref1[1] * ref2[5] + ref1[2] * ref2[9] + ref1[3] * ref2[13];
		result[2] = ref1[0] * ref2[2] + ref1[1] * ref2[6] + ref1[2] * ref2[10] + ref1[3] * ref2[14];
		result[3] = ref1[0] * ref2[3] + ref1[1] * ref2[7] + ref1[2] * ref2[11] + ref1[3] * ref2[15];

		result[4] = ref1[4] * ref2[0] + ref1[5] * ref2[4] + ref1[6] * ref2[8] + ref1[7] * ref2[12];
		result[5] = ref1[4] * ref2[1] + ref1[5] * ref2[5] + ref1[6] * ref2[9] + ref1[7] * ref2[13];
		result[6] = ref1[4] * ref2[2] + ref1[5] * ref2[6] + ref1[6] * ref2[10] + ref1[7] * ref2[14];
		result[7] = ref1[4] * ref2[3] + ref1[5] * ref2[7] + ref1[6] * ref2[11] + ref1[7] * ref2[15];

		result[8] = ref1[8] * ref2[0] + ref1[9] * ref2[4] + ref1[10] * ref2[8] + ref1[11] * ref2[12];
		result[9] = ref1[8] * ref2[1] + ref1[9] * ref2[5] + ref1[10] * ref2[9] + ref1[11] * ref2[13];
		result[10] = ref1[8] * ref2[2] + ref1[9] * ref2[6] + ref1[10] * ref2[10] + ref1[11] * ref2[14];
		result[11] = ref1[8] * ref2[3] + ref1[9] * ref2[7] + ref1[10] * ref2[11] + ref1[11] * ref2[15];

		result[12] = ref1[12] * ref2[0] + ref1[13] * ref2[4] + ref1[14] * ref2[8] + ref1[15] * ref2[12];
		result[13] = ref1[12] * ref2[1] + ref1[13] * ref2[5] + ref1[14] * ref2[9] + ref1[15] * ref2[13];
		result[14] = ref1[12] * ref2[2] + ref1[13] * ref2[6] + ref1[14] * ref2[10] + ref1[15] * ref2[14];
		result[15] = ref1[12] * ref2[3] + ref1[13] * ref2[7] + ref1[14] * ref2[11] + ref1[15] * ref2[15];

		return result;
	}

	function matrixToEuler(mat)
	{
		var result = [];

		theta = -Math.asin( mat[2]);
		cosTheta =  Math.cos( theta );
		theta = -radiansToDegrees(theta);

		if( Math.abs( cosTheta ) > 0.0005 )
		{
			tempX =  mat[10] / cosTheta;
			tempY = -mat[6]  / cosTheta;

			phi = Math.atan2( tempY, tempX );
			phi= radiansToDegrees(phi);

			tempX =  mat[0] / cosTheta;
			tempY = -mat[1] / cosTheta;

			psi = Math.atan2( tempY, tempX );
			psi = radiansToDegrees(psi);
		}
		// Gimaball Lock Proc
		else
		{
			phi = 0;

			tempX = mat[5];
			tempY = mat[4];

			psi = Math.atan2( tempY, tempX );
			psi = radiansToDegrees(psi);
		}

		result[0] = phi;
		result[1] = theta;
		result[2] = psi;

		return result;
	}

	function preBake(layer)
	{
		var result = 0;

		if(layer.position.selected) result++;
        if(layer.scale.selected) result++;
        if( (layer.orientation.selected) || (layer.rotation.selected) || (layer.xRotation.selected) || (layer.yRotation.selected) || (layer.zRotation.selected) ) result++;
		
		if(result == 0) result = 3;

		return result;
	}

	function bake(inLayer,outLayer)
	{
         var doPosition = false;
         var doScale = false;
         var doRotation = false;
		 
		 // if no params are selected then bake all transforms
		 // else just bake selected transforms
        if(outLayer.position.selected) doPosition = true;
        if(outLayer.scale.selected) doScale = true;
        if( (outLayer.orientation.selected) || (outLayer.rotation.selected) || (outLayer.xRotation.selected) || (outLayer.yRotation.selected) || (outLayer.zRotation.selected) ) doRotation = true;

        if(!doPosition && !doScale && !doRotation)
        {
            doPosition = true;
            doScale = true;
            doRotation = true;
        }
	 
		// bake position or scale
		if(doPosition || doScale)
		{
			if(inLayer.position.dimensionsSeparated)
			{
				if(inLayer.threeDLayer || inLayer instanceof CameraLayer || inLayer instanceof LightLayer)
					bakePositionScale3DSeperateDimensions(inLayer,outLayer,doPosition,doScale);
				else
					bakePositionScale2DSeperateDimensions(inLayer,outLayer,doPosition,doScale);
			}
			else
				bakePositionScale(inLayer,outLayer,doPosition,doScale);
		}
	 
         // bake a rotation
         if(doRotation)
         {
             if(inLayer.threeDLayer || inLayer instanceof CameraLayer || inLayer instanceof LightLayer)
                bake3DRotation(inLayer,outLayer);
            else
                bake2DRotation(inLayer,outLayer);
         }
	}

	function bake3DRotation(inLayer,outLayer)
	{
		var rotationXKeyValueArray = [];
		var rotationYKeyValueArray = [];
		var rotationZKeyValueArray = [];
		var rotationKeyTimeArray = [];

		var NextFrame=1/inLayer.containingComp.frameRate;
		
        var totalTime = EndBake - StartBake;
		var progressText = "Processing "  + outLayer.name + " Rotation";
		
		for (var i=StartBake; i<EndBake; i=i+NextFrame)
		{
			inLayer.containingComp.time = i;
			var tempLayer = inLayer.duplicate();
			tempLayer.parent = null;

			var resultAngles = [];
			var matRotationTot = [];
			var matOrientationTot = [];
			var matEndRotation = [];

			xRotMat = eulerToMatrix(degreesToRadians(tempLayer.rotationX.valueAtTime(i,false)),1,0,0);
			yRotMat = eulerToMatrix(degreesToRadians(tempLayer.rotationY.valueAtTime(i,false)),0,1,0);
			zRotMat = eulerToMatrix(degreesToRadians(tempLayer.rotationZ.valueAtTime(i,false)),0,0,1);
								
			matRotationTot = matrixMultiply(xRotMat,matrixMultiply(yRotMat,zRotMat));

			xOriMat = eulerToMatrix(degreesToRadians(tempLayer.orientation.valueAtTime(i,false)[0]),1,0,0);
			yOriMat = eulerToMatrix(degreesToRadians(tempLayer.orientation.valueAtTime(i,false)[1]),0,1,0);
			zOriMat = eulerToMatrix(degreesToRadians(tempLayer.orientation.valueAtTime(i,false)[2]),0,0,1);

			matOrientationTot = matrixMultiply(xOriMat, matrixMultiply(yOriMat, zOriMat));

			matEndRotation = matrixMultiply(matOrientationTot, matRotationTot);

			resultAngles = matrixToEuler(matEndRotation);
			
			rotationZKeyValueArray[rotationZKeyValueArray.length] = resultAngles[2];
			rotationYKeyValueArray[rotationYKeyValueArray.length] = resultAngles[1];
			rotationXKeyValueArray[rotationXKeyValueArray.length] = resultAngles[0];
			rotationKeyTimeArray[rotationKeyTimeArray.length] = i;
            
			tempLayer.remove();
			  
			progTime += NextFrame;
			updateProgBar(progBarUI,false,progTime,totalDurationToBake,"Total Progress"); //update the bar: (progBarUI,barValue,barMaxValue,progressText) 
            updateProgBar(progBarUI,true,(i-StartBake),totalTime,progressText); //update the bar: (progBarUI,barValue,barMaxValue,progressText) 
		}
	
		while(outLayer.rotationX.numKeys > 0)
			outLayer.rotationX.removeKey(outLayer.rotationX.numKeys);

		while(outLayer.rotationY.numKeys > 0)
			outLayer.rotationY.removeKey(outLayer.rotationY.numKeys);

		while(outLayer.rotationZ.numKeys > 0)
			outLayer.rotationZ.removeKey(outLayer.rotationZ.numKeys);

		while(outLayer.orientation.numKeys > 0)
			outLayer.orientation.removeKey(outLayer.orientation.numKeys);
		
        try
        {
            outLayer.rotationZ.setValuesAtTimes(rotationKeyTimeArray,rotationZKeyValueArray);
            outLayer.rotationZ.expressionEnabled = false;

            outLayer.rotationY.setValuesAtTimes(rotationKeyTimeArray,rotationYKeyValueArray);
            outLayer.rotationY.expressionEnabled = false;

            outLayer.rotationX.setValuesAtTimes(rotationKeyTimeArray,rotationXKeyValueArray);
            outLayer.rotationX.expressionEnabled = false;
            
             outLayer.orientation.setValue([0,0,0]);
             outLayer.orientation.expressionEnabled = false;
        }
        catch(err) {}

	}

	function bake2DRotation(inLayer,outLayer)
	{
		var rotationValueArray = [];
		var keyTimeArray = [];

		var NextFrame=1/inLayer.containingComp.frameRate;
		
        var totalTime = EndBake - StartBake;
		var progressText = "Processing "  + outLayer.name + " Rotation";
		
		for (var i=StartBake; i<EndBake; i=i+NextFrame)
		{
			inLayer.containingComp.time = i;
			var tempLayer = inLayer.duplicate();
			tempLayer.parent = null;
			
			rotationValueArray[rotationValueArray.length] = tempLayer.rotation.valueAtTime(i, false);
			keyTimeArray[keyTimeArray.length] = i;
			
			tempLayer.remove();
			  
			progTime += NextFrame;
			updateProgBar(progBarUI,false,progTime,totalDurationToBake,"Total Progress"); //update the bar: (progBarUI,barValue,barMaxValue,progressText) 
            updateProgBar(progBarUI,true,(i-StartBake),totalTime,progressText); //update the bar: (progBarUI,barValue,barMaxValue,progressText) 
		}

		while(outLayer.rotation.numKeys > 0)
			outLayer.rotation.removeKey(outLayer.rotation.numKeys);

        try
        {
            outLayer.rotation.setValuesAtTimes(keyTimeArray, rotationValueArray);
            outLayer.rotation.expressionEnabled = false;
        }
        catch(err) {}
    }

	function bakePositionScale(inLayer,outLayer,doPosition,doScale)
	{
		var positionValueArray = [];
		var scaleValueArray = [];
		var keyTimeArray = [];
        
        var NextFrame=1/inLayer.containingComp.frameRate;		
		
        var totalTime = EndBake - StartBake;
		var progressText = "Processing " + outLayer.name + (doPosition?(doScale?" Position and Scale":" Position"):" Scale");
        
        // get the keys to bake in
        for (var i=StartBake; i<EndBake; i=i+NextFrame)
        {
			inLayer.containingComp.time = i;
            var tempLayer = inLayer.duplicate();
            tempLayer.parent = null;

            positionValueArray[positionValueArray.length] = tempLayer.position.valueAtTime(i,false);
            scaleValueArray[scaleValueArray.length] = tempLayer.scale.valueAtTime(i,false);
            keyTimeArray[keyTimeArray.length] = i;

            tempLayer.remove();
            
			if(doPosition) progTime += NextFrame;
			if(doScale) progTime += NextFrame;
			updateProgBar(progBarUI,false,progTime,totalDurationToBake,"Total Progress"); //update the bar: (progBarUI,barValue,barMaxValue,progressText) 
             updateProgBar(progBarUI,true,(i-StartBake),totalTime,progressText); //update the bar: (progBarUI,barValue,barMaxValue,progressText) 
		}

        if(doPosition)
        {
			// remove all position keys
            while(outLayer.position.numKeys > 0)
				outLayer.position.removeKey(outLayer.position.numKeys);

			// set the position keys
            try
            {
                outLayer.position.setValuesAtTimes(keyTimeArray, positionValueArray);
                outLayer.position.expressionEnabled = false;
            }
            catch(err) {}
		}

		if(doScale)
        {
			// remove all scale keys
			while(outLayer.scale.numKeys > 0)
				outLayer.scale.removeKey(outLayer.scale.numKeys);

			// set the scale keys
            try
            {
                outLayer.scale.setValuesAtTimes(keyTimeArray, scaleValueArray);
                outLayer.scale.expressionEnabled = false;
            }
            catch(err) {}
		}
	}
	
	function bakePositionScale2DSeperateDimensions(inLayer,outLayer,doPosition,doScale)
	{
		var positionXValueArray = [];
		var positionYValueArray = [];
		var scaleValueArray = [];
		var keyTimeArray = [];

		var NextFrame=1/inLayer.containingComp.frameRate;
		
        var totalTime = EndBake - StartBake;
		var progressText = "Processing " + outLayer.name + (doPosition?(doScale?" Position and Scale":" Position"):" Scale");
		
		for (var i=StartBake; i<EndBake; i=i+NextFrame)
		{
			inLayer.containingComp.time = i;
            var tempLayer = inLayer.duplicate();
            tempLayer.parent = null;

			positionXValueArray[positionXValueArray.length] = tempLayer.position.getSeparationFollower(0).valueAtTime(i, false);
			positionYValueArray[positionYValueArray.length] = tempLayer.position.getSeparationFollower(1).valueAtTime(i, false);

			scaleValueArray[scaleValueArray.length] = tempLayer.scale.valueAtTime(i,false);
              keyTimeArray[keyTimeArray.length] = i;

			tempLayer.remove();
			
			if(doPosition) progTime += NextFrame;
			if(doScale) progTime += NextFrame;
			updateProgBar(progBarUI,false,progTime,totalDurationToBake,"Total Progress"); //update the bar: (progBarUI,barValue,barMaxValue,progressText) 
            updateProgBar(progBarUI,true,(i-StartBake),totalTime,progressText); //update the bar: (progBarUI,barValue,barMaxValue,progressText) 
		}

		if(doPosition)
        {
			// remove all position keys
			while(outLayer.position.getSeparationFollower(0).numKeys > 0)
				outLayer.position.getSeparationFollower(0).removeKey(outLayer.position.getSeparationFollower(0).numKeys);

			while(outLayer.position.getSeparationFollower(1).numKeys > 0)
				outLayer.position.getSeparationFollower(1).removeKey(outLayer.position.getSeparationFollower(1).numKeys);

			// set the position keys
            try
            {
                outLayer.position.getSeparationFollower(0).setValuesAtTimes(keyTimeArray, positionXValueArray);
                outLayer.position.getSeparationFollower(0).expressionEnabled = false;

                outLayer.position.getSeparationFollower(1).setValuesAtTimes(keyTimeArray, positionYValueArray);
                outLayer.position.getSeparationFollower(1).expressionEnabled = false;
            }
            catch(err) {}
		}

		if(doScale)
        {
			// remove all scale keys
			while(outLayer.scale.numKeys > 0)
				outLayer.scale.removeKey(outLayer.scale.numKeys);

			// set the scale keys
            try
            {
                outLayer.scale.setValuesAtTimes(keyTimeArray, scaleValueArray);
                outLayer.scale.expressionEnabled = false;
            }
            catch(err) {}        
		}
	}

	function bakePositionScale3DSeperateDimensions(inLayer,outLayer,doPosition,doScale)
	{
		var positionXValueArray = [];
		var positionYValueArray = [];
		var positionZValueArray = [];
		var scaleValueArray = [];
		var keyTimeArray = [];

		var NextFrame=1/inLayer.containingComp.frameRate;
		
        var totalTime = EndBake - StartBake;
		var progressText = "Processing " + outLayer.name + (doPosition?(doScale?" Position and Scale":" Position"):" Scale");
		
		for (var i=StartBake; i<EndBake; i=i+NextFrame)
		{
			inLayer.containingComp.time = i;
            var tempLayer = inLayer.duplicate();
            tempLayer.parent = null;

			positionXValueArray[positionXValueArray.length] = tempLayer.position.getSeparationFollower(0).valueAtTime(i, false);
			positionYValueArray[positionYValueArray.length] = tempLayer.position.getSeparationFollower(1).valueAtTime(i, false);
			positionZValueArray[positionZValueArray.length] = tempLayer.position.getSeparationFollower(2).valueAtTime(i, false);

			scaleValueArray[scaleValueArray.length] = tempLayer.scale.valueAtTime(i,false);
              keyTimeArray[keyTimeArray.length] = i;

			tempLayer.remove();
			
			if(doPosition) progTime += NextFrame;
			if(doScale) progTime += NextFrame;
			updateProgBar(progBarUI,false,progTime,totalDurationToBake,"Total Progress"); //update the bar: (progBarUI,barValue,barMaxValue,progressText) 
            updateProgBar(progBarUI,true,(i-StartBake),totalTime,progressText); //update the bar: (progBarUI,barValue,barMaxValue,progressText) 
		}

		if(doPosition)
        {
			// remove all position keys
			while(outLayer.position.getSeparationFollower(0).numKeys > 0)
				outLayer.position.getSeparationFollower(0).removeKey(outLayer.position.getSeparationFollower(0).numKeys);

			while(outLayer.position.getSeparationFollower(1).numKeys > 0)
				outLayer.position.getSeparationFollower(1).removeKey(outLayer.position.getSeparationFollower(1).numKeys);

			while(outLayer.position.getSeparationFollower(2).numKeys > 0)
				outLayer.position.getSeparationFollower(2).removeKey(outLayer.position.getSeparationFollower(2).numKeys);

			// set the position keys
            try
            {
                outLayer.position.getSeparationFollower(0).setValuesAtTimes(keyTimeArray, positionXValueArray);
                outLayer.position.getSeparationFollower(0).expressionEnabled = false;

                outLayer.position.getSeparationFollower(1).setValuesAtTimes(keyTimeArray, positionYValueArray);
                outLayer.position.getSeparationFollower(1).expressionEnabled = false;

                outLayer.position.getSeparationFollower(2).setValuesAtTimes(keyTimeArray, positionZValueArray);
                outLayer.position.getSeparationFollower(2).expressionEnabled = false;
            }
            catch(err) {}
		}

		if(doScale)
        {
			// remove all scale keys
			while(outLayer.scale.numKeys > 0)
				outLayer.scale.removeKey(outLayer.scale.numKeys);

			// set the scale keys
            try
            {
                outLayer.scale.setValuesAtTimes(keyTimeArray, scaleValueArray);
                outLayer.scale.expressionEnabled = false;
            }
            catch(err) {}
		}
	}

	function axisToRotation(inMatrix) // make sure to normalize vectors!
	{
		var resultAngles = [];

		xAxis = [ inMatrix[0],inMatrix[1],inMatrix[2] ];
		yAxis = [ inMatrix[3],inMatrix[4],inMatrix[5] ];
		zAxis = [ inMatrix[6],inMatrix[7],inMatrix[8] ];
		resultAngles[0] = radiansToDegrees( Math.atan2(yAxis[2],xAxis[2]) );
		resultAngles[1] = radiansToDegrees( Math.asin(-zAxis[2]) );
		resultAngles[2] = radiansToDegrees( Math.atan2(zAxis[1],zAxis[0]) );

		return resultAngles;
	}

	function axisToRotation(inXAxis, inYAxis, inZAxis, translation) // make sure to normalize vectors!
	{
		var xAxis = normalize(inXAxis);
		var yAxis = normalize(inYAxis);
		var zAxis = normalize(inZAxis);	
		var result = [];
		
		result[0] = xAxis[0];
		result[1] = yAxis[0];
		result[2] = zAxis[0];
		result[3] = translation[0];

		result[4] = xAxis[1]
		result[5] = yAxis[1]
		result[6] = zAxis[1]
		result[7] = translation[1]

		result[8] = xAxis[2]
		result[9] = yAxis[2]
		result[10] = zAxis[2]
		result[11] = translation[2]

		result[12] = 0;
		result[13] = 0;
		result[14] = 0;
		result[15] = 1;

		return result;
	}

	function normalize(inVector)
	{
		var outVector = [];
		
		magnitude = Math.sqrt(inVector[0] * inVector[0] + inVector[1] * inVector[1] + inVector[2] * inVector[2]);
		
		outVector[0] = inVector[0] / magnitude;
		outVector[1] = inVector[1] / magnitude;
		outVector[2] = inVector[2] / magnitude;
		
		return outVector;
	}

	function axisToRotation(inMatrix) // make sure to normalize vectors!
	{
		var resultAngles = [];

		xAxis = [ inMatrix[0],inMatrix[1],inMatrix[2], 0 ];
		yAxis = [ inMatrix[3],inMatrix[4],inMatrix[5], 0 ];
		zAxis = [ inMatrix[6],inMatrix[7],inMatrix[8], 0 ];

		resultAngles[0] = radiansToDegrees( Math.atan2(yAxis[2],xAxis[2]) );
		resultAngles[1] = radiansToDegrees( Math.asin(-zAxis[2]) );
		resultAngles[2] = radiansToDegrees( Math.atan2(zAxis[1],zAxis[0]) );

		return resultAngles;
	}

	function main()
	{
		app.beginUndoGroup("bakeParentedTransform");
		
        if(proj)
        {
            if(proj.numItems > 0)
            {
                var myComp = proj.activeItem;
				
                if(myComp && myComp instanceof CompItem)
                {
                    var target = myComp.selectedLayers;
                    
                    if(target.length > 0)
                    {
                        var originalTime = myComp.time;
						if(originalTime<0) originalTime = 0;
						StartBake = myComp.workAreaStart;
						EndBake = myComp.workAreaStart + myComp.workAreaDuration;

						var progCount = 0;
						for( var i = 0 ; i < target.length ; i++)
						{
							if(!(target[i].hasAudio && !target[i].hasVideo))	// do not process audio layers
								progCount += preBake(target[i]);
						}
						totalDurationToBake = progCount*myComp.workAreaDuration;
                        
                        progBarUI.show();  //show it 
						updateProgBar(progBarUI,false,0.01,totalDurationToBake,"Total Progress"); //update the bar: (progBarUI,barValue,barMaxValue,progressText) 
                        for( var j = 0 ; j < target.length ; j++)
                        {
							if(!(target[j].hasAudio && !target[j].hasVideo))	// do not process audio layers
							{
								var dupeLayer = target[j].duplicate();
								target[j].parent = null;
								bake(dupeLayer,target[j]);
								dupeLayer.remove();
							}
                        }
						updateProgBar(progBarUI,false,1,1,"Total Progress"); // a momentary display of completion
                        progBarUI.close();  //close it 
                        
                        myComp.time = originalTime;
                    }
                    else
                        alert("Please select layer(s) or a layer transform(s) within an active comp!");
                }
                else
                    alert("Please select layer(s) or a layer transform(s) within an active comp!");
            }
            else
                alert("Please select layer(s) or a layer transform(s) within an active comp!");
		}
        else
            alert("Please select layer(s) or a layer transform(s) within an active comp!");

		app.endUndoGroup();
	}

	main();
}