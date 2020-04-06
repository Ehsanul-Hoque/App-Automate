package com.ehsanfahad.appautomate;

import androidx.appcompat.app.AppCompatActivity;
import androidx.core.content.ContextCompat;

import android.os.Bundle;
import android.widget.ImageView;
import android.widget.TextView;


public class MainActivity extends AppCompatActivity
{

    private TextView textView;
    private ImageView imageView;


    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        textView = findViewById(R.id.textView);
        imageView = findViewById(R.id.imageView);
        showInfo();
    }


    private void showInfo()
    {
        String info = "app name: " + BuildConfig.APP_NAME;
        info += "\npackage name: " + getPackageName();
        info += "\ntheme color: #" + Integer.toHexString(ContextCompat.getColor(this, R.color.colorPrimary));

        textView.setText(info);
        imageView.setImageResource(R.drawable.app_icon);
    }

}
